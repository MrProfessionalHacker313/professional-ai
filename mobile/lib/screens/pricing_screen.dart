import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';

class PricingScreen extends StatelessWidget {
  const PricingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pricing Plans'),
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
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _PlanCard(
              title: 'Free',
              price: '\$0',
              period: '/month',
              features: ['3 Code generations/day', '50 Chat messages/day', '1 Video/day', '10 Images/day', '3 Animations/day'],
              color: const Color(0xFF94A3B8),
              onTap: () {},
            ),
            const SizedBox(height: 12),
            _PlanCard(
              title: 'Pro',
              price: '\$9.99',
              period: '/month',
              features: ['Unlimited Code', 'Unlimited Chat', '10 Videos/day', '50 Images/day', '20 Animations/day', 'Priority support'],
              color: const Color(0xFF06B6D4),
              highlighted: true,
              onTap: () => _handleSubscribe(context, 'pro'),
            ),
            const SizedBox(height: 12),
            _PlanCard(
              title: 'Enterprise',
              price: '\$99.99',
              period: '/month',
              features: ['Everything in Pro', 'Unlimited Media', 'Admin Panel', 'Custom AI Models', 'Dedicated Support', 'SLA Guarantee'],
              color: const Color(0xFF8B5CF6),
              onTap: () => _handleSubscribe(context, 'enterprise'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleSubscribe(BuildContext context, String plan) async {
    try {
      final result = await ApiService.instance.subscribe(plan);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? 'Subscription updated')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Subscription failed: $e')),
        );
      }
    }
  }
}

class _PlanCard extends StatelessWidget {
  final String title;
  final String price;
  final String period;
  final List<String> features;
  final Color color;
  final bool highlighted;
  final VoidCallback onTap;

  const _PlanCard({
    required this.title,
    required this.price,
    required this.period,
    required this.features,
    required this.color,
    this.highlighted = false,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: highlighted ? color : const Color(0xFF334155),
            width: highlighted ? 2 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: highlighted ? color : Colors.white,
                  ),
                ),
                Row(
                  children: [
                    Text(
                      price,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: color,
                      ),
                    ),
                    Text(
                      period,
                      style: const TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...features.map(
              (feature) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Icon(Icons.check_circle, size: 16, color: color),
                    const SizedBox(width: 8),
                    Expanded(child: Text(feature, style: const TextStyle(color: Color(0xFFE2E8F0)))),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
