
import 'dart:async';

import 'package:flutter/material.dart';

import 'achievements_page.dart';
import 'app_controller.dart';
import 'app_theme.dart';
import 'gallery_page.dart';
import 'history_page.dart';
import 'home_page.dart';
import 'i18n.dart';
import 'settings_page.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key, required this.controller});
  final AppController controller;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int index = 0;
  final List<AppNotification> _queue = <AppNotification>[];
  AppNotification? _current;
  bool _notificationVisible = false;
  Timer? _notificationTimer;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onController);
    WidgetsBinding.instance.addPostFrameCallback((_) => _onController());
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onController);
    _notificationTimer?.cancel();
    super.dispose();
  }

  void _onController() {
    if (!mounted) return;
    final items = widget.controller.popPendingNotifications();
    if (items.isNotEmpty) {
      _queue.addAll(items);
    }

    final level = widget.controller.popLevelUp();
    if (level != null) {
      _queue.add(
        AppNotification(
          kind: AppNotificationKind.level,
          title: 'LEVEL UP!',
          message: 'You reached level $level. Keep grinding!',
        ),
      );
    }

    _showNextNotification();
  }

  void _showNextNotification() {
    if (_current != null || _queue.isEmpty || !mounted) return;
    setState(() {
      _current = _queue.removeAt(0);
      _notificationVisible = true;
    });

    _notificationTimer?.cancel();
    _notificationTimer = Timer(const Duration(milliseconds: 3300), () {
      if (!mounted) return;
      setState(() => _notificationVisible = false);
      _notificationTimer = Timer(const Duration(milliseconds: 320), () {
        if (!mounted) return;
        setState(() => _current = null);
        _showNextNotification();
      });
    });
  }

  void _dismissNotification() {
    _notificationTimer?.cancel();
    if (!mounted) return;
    setState(() => _notificationVisible = false);
    _notificationTimer = Timer(const Duration(milliseconds: 260), () {
      if (!mounted) return;
      setState(() => _current = null);
      _showNextNotification();
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final pages = <Widget>[
      HomePage(controller: widget.controller),
      HistoryPage(controller: widget.controller),
      GalleryPage(controller: widget.controller),
      AchievementsPage(controller: widget.controller),
    ];

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: <Color>[c.bgTop, c.bgBottom]),
      ),
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            Scaffold(
              backgroundColor: Colors.transparent,
              body: Column(
                children: <Widget>[
                  Padding(
                    padding: const EdgeInsets.fromLTRB(28, 24, 28, 16),
                    child: Row(
                      children: <Widget>[
                        Expanded(
                          child: FittedBox(
                            alignment: Alignment.centerLeft,
                            fit: BoxFit.scaleDown,
                            child: Text(l.appName, maxLines: 1, style: const TextStyle(fontSize: 40, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 4)),
                          ),
                        ),
                        IconButton(
                          iconSize: 30,
                          onPressed: () {
                            widget.controller.checkDeadlineStatus();
                            widget.controller.notifyAction('ACTION CONFIRMED!', 'Notification check finished.');
                          },
                          icon: const Icon(Icons.notifications),
                        ),
                        const SizedBox(width: 8),
                        IconButton(iconSize: 32, onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SettingsPage(controller: widget.controller))), icon: const Icon(Icons.settings)),
                      ],
                    ),
                  ),
                  Padding(padding: const EdgeInsets.symmetric(horizontal: 28), child: Container(height: 4, color: c.line.withValues(alpha: 0.9))),
                  const SizedBox(height: 14),
                  Expanded(child: pages[index]),
                ],
              ),
              bottomNavigationBar: Container(
                decoration: BoxDecoration(color: c.bgTop.withValues(alpha: 0.72), borderRadius: const BorderRadius.vertical(top: Radius.circular(26))),
                child: NavigationBar(
                  backgroundColor: Colors.transparent,
                  selectedIndex: index,
                  onDestinationSelected: (v) => setState(() => index = v),
                  destinations: <NavigationDestination>[
                    NavigationDestination(icon: const Icon(Icons.home), label: l.homework),
                    NavigationDestination(icon: const Icon(Icons.history), label: l.history),
                    NavigationDestination(icon: const Icon(Icons.photo_library), label: l.gallery),
                    NavigationDestination(icon: const Icon(Icons.emoji_events), label: l.achievements),
                  ],
                ),
              ),
            ),
            if (_current != null)
              Positioned(
                left: 16,
                right: 16,
                top: 8,
                child: AnimatedSlide(
                  duration: const Duration(milliseconds: 280),
                  curve: Curves.easeOutBack,
                  offset: _notificationVisible ? Offset.zero : const Offset(0, -1.25),
                  child: AnimatedOpacity(
                    duration: const Duration(milliseconds: 220),
                    opacity: _notificationVisible ? 1 : 0,
                    child: DoxelOverlayNotification(
                      notification: _current!,
                      onClose: _dismissNotification,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class DoxelOverlayNotification extends StatelessWidget {
  const DoxelOverlayNotification({super.key, required this.notification, required this.onClose});
  final AppNotification notification;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    final accent = _accent(notification.kind);
    final icon = _icon(notification.kind);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onClose,
        child: Container(
          padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
          decoration: BoxDecoration(
            color: c.panel.withValues(alpha: 0.98),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: accent, width: 1.5),
            boxShadow: <BoxShadow>[BoxShadow(color: accent.withValues(alpha: 0.18), blurRadius: 24, spreadRadius: 1, offset: const Offset(0, 10))],
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: c.text, width: 3)),
                child: Icon(icon, color: c.text, size: 32),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      notification.title.toUpperCase(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 16, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 1.7, color: c.text),
                    ),
                    const SizedBox(height: 4),
                    Container(height: 2, width: 230, color: c.line.withValues(alpha: 0.8)),
                    const SizedBox(height: 7),
                    Text(
                      notification.message,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 12, height: 1.15, fontWeight: FontWeight.w800, letterSpacing: 0.7, color: c.text),
                    ),
                    const SizedBox(height: 6),
                    Align(
                      alignment: Alignment.centerRight,
                      child: Text(
                        _formatOverlayTime(notification.occurredAt),
                        style: TextStyle(fontSize: 11, height: 1.0, fontWeight: FontWeight.w900, color: c.muted, letterSpacing: 0.7),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              Icon(Icons.close, size: 18, color: c.muted),
            ],
          ),
        ),
      ),
    );
  }

  Color _accent(AppNotificationKind kind) {
    switch (kind) {
      case AppNotificationKind.achievement:
        return const Color(0xFFFFC400);
      case AppNotificationKind.error:
        return const Color(0xFFFF2D55);
      case AppNotificationKind.action:
        return const Color(0xFF00FF39);
      case AppNotificationKind.deadline:
        return const Color(0xFFFF9F0A);
      case AppNotificationKind.level:
        return const Color(0xFF00D1FF);
    }
  }

  IconData _icon(AppNotificationKind kind) {
    switch (kind) {
      case AppNotificationKind.achievement:
        return Icons.workspace_premium;
      case AppNotificationKind.error:
        return Icons.block;
      case AppNotificationKind.action:
        return Icons.check;
      case AppNotificationKind.deadline:
        return Icons.access_time_filled;
      case AppNotificationKind.level:
        return Icons.auto_awesome;
    }
  }

  String _formatOverlayTime(DateTime value) {
    String two(int v) => v.toString().padLeft(2, '0');
    return '${two(value.day)}/${two(value.month)}/${value.year} ${two(value.hour)}:${two(value.minute)}';
  }
}
