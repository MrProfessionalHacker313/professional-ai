import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class AdminScreen extends StatelessWidget {
  const AdminScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Panel'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0B1220), Color(0xFF1E3A5F)],
          ),
        ),
        child: FutureBuilder<Map<String, dynamic>>(
          future: ApiService.instance.getAdminStats(),
          builder: (context, snapshot) {
            if (!snapshot.hasData) {
              return const Center(
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF06B6D4)),
                ),
              );
            }

            final stats = snapshot.data!;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _AdminCard(
                  title: 'Total Users',
                  value: stats['totalUsers']?.toString() ?? '0',
                  icon: Icons.people,
                  color: const Color(0xFF06B6D4),
                ),
                const SizedBox(height: 12),
                _AdminCard(
                  title: 'Revenue',
                  value: '\$${stats['revenue'] ?? '0'}',
                  icon: Icons.attach_money,
                  color: const Color(0xFF10B981),
                ),
                const SizedBox(height: 12),
                _AdminCard(
                  title: 'Active Sessions',
                  value: stats['activeSessions']?.toString() ?? '0',
                  icon: Icons.power,
                  color: const Color(0xFFF59E0B),
                ),
                const SizedBox(height: 12),
                _AdminCard(
                  title: 'System Health',
                  value: stats['systemHealth'] ?? 'OK',
                  icon: Icons.health_and_safety,
                  color: const Color(0xFF8B5CF6),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _AdminCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _AdminCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 32, color: color),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontSize: 14, color: Color(0xFF94A3B8)),
                ),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
