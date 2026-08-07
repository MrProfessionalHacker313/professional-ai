#!/usr/bin/env python3
"""
Health Check & Auto-Restart Service
Monitors all self-hosted models every 60 seconds
Automatically restarts failed services via Docker/systemd
"""

import asyncio
import subprocess
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    """Health status of a service"""
    name: str
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int = 0
    last_restart: Optional[datetime] = None
    restart_count: int = 0
    error_message: Optional[str] = None


class HealthCheckService:
    """
    Monitors all services and auto-restarts failed ones
    - Checks every 60 seconds
    - Marks unhealthy after 3 consecutive failures
    - Auto-restarts via Docker/systemd
    - Prevents restart loops (max 5 restarts per hour)
    """

    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.check_interval = 60  # seconds
        self.failure_threshold = 3
        self.max_restarts_per_hour = 5
        self.restart_cooldown = timedelta(minutes=10)
        self._running = False
        
        # Define all services to monitor
        self.service_definitions = {
            "ollama": {
                "url": "http://localhost:11434/api/tags",
                "docker_container": "pro-ai-ollama",
                "systemd_service": "ollama",
                "type": "docker"
            },
            "comfyui": {
                "url": "http://localhost:8188/system_stats",
                "docker_container": "pro-ai-comfyui",
                "systemd_service": None,
                "type": "docker"
            },
            "whisper": {
                "url": "http://localhost:8001/health",
                "docker_container": "pro-ai-whisper",
                "systemd_service": None,
                "type": "docker"
            },
            "piper-tts": {
                "url": "http://localhost:8002/health",
                "docker_container": "pro-ai-piper",
                "systemd_service": None,
                "type": "docker"
            },
            "searxng": {
                "url": "http://localhost:8888/",
                "docker_container": "pro-ai-searxng",
                "systemd_service": None,
                "type": "docker"
            },
            "postgres": {
                "url": None,  # Special handling
                "docker_container": "pro-ai-postgres",
                "systemd_service": None,
                "type": "docker"
            },
            "redis": {
                "url": None,  # Special handling
                "docker_container": "pro-ai-redis",
                "systemd_service": None,
                "type": "docker"
            },
            "backend": {
                "url": "http://localhost:8000/api/health",
                "docker_container": "pro-ai-backend",
                "systemd_service": None,
                "type": "docker"
            },
            "frontend": {
                "url": "http://localhost:3000",
                "docker_container": "pro-ai-frontend",
                "systemd_service": None,
                "type": "docker"
            }
        }
        
        # Initialize service health
        for service_name in self.service_definitions.keys():
            self.services[service_name] = ServiceHealth(
                name=service_name,
                is_healthy=True,
                last_check=datetime.utcnow()
            )

    async def start(self):
        """Start the health check loop"""
        self._running = True
        logger.info("Health check service started")
        await self._run()

    async def stop(self):
        """Stop the health check loop"""
        self._running = False
        logger.info("Health check service stopped")

    async def _run(self):
        """Main loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_services(self):
        """Check health of all services"""
        tasks = []
        for service_name in self.service_definitions.keys():
            tasks.append(self._check_service(service_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, ServiceHealth):
                self._update_service_health(result)

    async def _check_service(self, service_name: str) -> ServiceHealth:
        """Check health of a single service"""
        service_def = self.service_definitions[service_name]
        start_time = time.time()
        
        try:
            is_healthy = False
            error_message = None
            
            # Special handling for databases
            if service_name == "postgres":
                is_healthy = await self._check_postgres()
            elif service_name == "redis":
                is_healthy = await self._check_redis()
            elif service_def["url"]:
                is_healthy = await self._check_http(service_def["url"])
            else:
                error_message = "No health check URL defined"
            
            response_time = time.time() - start_time
            
            return ServiceHealth(
                name=service_name,
                is_healthy=is_healthy,
                last_check=datetime.utcnow(),
                error_message=error_message if not is_healthy else None
            )
            
        except Exception as e:
            return ServiceHealth(
                name=service_name,
                is_healthy=False,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def _check_http(self, url: str, timeout: int = 10) -> bool:
        """Check HTTP service health"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"HTTP check failed for {url}: {e}")
            return False

    async def _check_postgres(self) -> bool:
        """Check PostgreSQL health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:5432")
                # PostgreSQL doesn't have HTTP endpoint, check via docker
                result = subprocess.run(
                    ["docker", "exec", "pro-ai-postgres", "pg_isready", "-U", "postgres"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
        except Exception as e:
            logger.debug(f"PostgreSQL check failed: {e}")
            return False

    async def _check_redis(self) -> bool:
        """Check Redis health"""
        try:
            result = subprocess.run(
                ["docker", "exec", "pro-ai-redis", "redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and "PONG" in result.stdout
        except Exception as e:
            logger.debug(f"Redis check failed: {e}")
            return False

    def _update_service_health(self, health: ServiceHealth):
        """Update service health and trigger restart if needed"""
        service_name = health.name
        current_health = self.services[service_name]
        
        if health.is_healthy:
            # Service is healthy
            if not current_health.is_healthy:
                logger.info(f"✓ {service_name} recovered")
            
            current_health.is_healthy = True
            current_health.consecutive_failures = 0
            current_health.error_message = None
        else:
            # Service is unhealthy
            current_health.consecutive_failures += 1
            current_health.error_message = health.error_message
            
            logger.warning(
                f"✗ {service_name} unhealthy (failures: {current_health.consecutive_failures}/{self.failure_threshold})"
            )
            
            # Check if we should restart
            if current_health.consecutive_failures >= self.failure_threshold:
                if self._should_restart(service_name, current_health):
                    self._restart_service(service_name)
                else:
                    logger.error(
                        f"⚠ {service_name} needs restart but rate-limited or in cooldown"
                    )
        
        current_health.last_check = health.last_check

    def _should_restart(self, service_name: str, health: ServiceHealth) -> bool:
        """Check if service should be restarted"""
        # Check cooldown period
        if health.last_restart:
            time_since_restart = datetime.utcnow() - health.last_restart
            if time_since_restart < self.restart_cooldown:
                logger.info(
                    f"{service_name} in cooldown period ({time_since_restart.seconds}s < {self.restart_cooldown.seconds}s)"
                )
                return False
        
        # Check restart rate limit
        if health.restart_count >= self.max_restarts_per_hour:
            logger.error(
                f"{service_name} hit max restarts per hour ({self.max_restarts_per_hour})"
            )
            return False
        
        return True

    def _restart_service(self, service_name: str):
        """Restart a service"""
        service_def = self.service_definitions[service_name]
        health = self.services[service_name]
        
        logger.warning(f"🔄 Restarting {service_name}...")
        
        try:
            if service_def["type"] == "docker" and service_def["docker_container"]:
                self._restart_docker_container(service_def["docker_container"])
            elif service_def["type"] == "systemd" and service_def["systemd_service"]:
                self._restart_systemd_service(service_def["systemd_service"])
            else:
                logger.error(f"Unknown service type for {service_name}")
                return
            
            # Update restart tracking
            health.last_restart = datetime.utcnow()
            health.restart_count += 1
            health.consecutive_failures = 0
            
            logger.info(f"✓ {service_name} restarted successfully (restart #{health.restart_count})")
            
            # Wait for service to come back up
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")

    def _restart_docker_container(self, container_name: str):
        """Restart a Docker container"""
        try:
            # Restart the container
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Docker restart failed: {result.stderr}")
                # Try to start if not running
                subprocess.run(
                    ["docker", "start", container_name],
                    capture_output=True,
                    timeout=30
                )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Docker restart timed out for {container_name}")
        except Exception as e:
            logger.error(f"Error restarting Docker container {container_name}: {e}")

    def _restart_systemd_service(self, service_name: str):
        """Restart a systemd service"""
        try:
            subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
        except Exception as e:
            logger.error(f"Error restarting systemd service {service_name}: {e}")

    def get_health_report(self) -> Dict:
        """Get health report of all services"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "healthy",
            "services": {}
        }
        
        unhealthy_count = 0
        for service_name, health in self.services.items():
            report["services"][service_name] = {
                "is_healthy": health.is_healthy,
                "last_check": health.last_check.isoformat(),
                "consecutive_failures": health.consecutive_failures,
                "restart_count": health.restart_count,
                "last_restart": health.last_restart.isoformat() if health.last_restart else None,
                "error_message": health.error_message
            }
            
            if not health.is_healthy:
                unhealthy_count += 1
        
        if unhealthy_count > 0:
            report["overall_health"] = "degraded" if unhealthy_count < len(self.services) / 2 else "unhealthy"
            report["unhealthy_count"] = unhealthy_count
            report["total_count"] = len(self.services)
        
        return report


async def main():
    """Main entry point"""
    health_service = HealthCheckService()
    
    try:
        await health_service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await health_service.stop()


if __name__ == "__main__":
    asyncio.run(main())