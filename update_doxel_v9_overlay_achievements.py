from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "lib" / "src"
PUBSPEC = ROOT / "pubspec.yaml"

if not PUBSPEC.exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current Flutter project.")


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v9")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


def ensure_dependency(name: str, version: str) -> None:
    text = read(PUBSPEC)
    pattern = rf"^\s{{2}}{re.escape(name)}:\s*.*$"
    if re.search(pattern, text, flags=re.M):
        text = re.sub(pattern, f"  {name}: {version}", text, flags=re.M)
    else:
        m = re.search(r"^dependencies:\s*$", text, flags=re.M)
        if not m:
            text += "\n\ndependencies:\n  flutter:\n    sdk: flutter\n"
            m = re.search(r"^dependencies:\s*$", text, flags=re.M)
        text = text[:m.end()] + f"\n  {name}: {version}" + text[m.end():]
    PUBSPEC.write_text(text, encoding="utf-8")


MODELS = r'''
import 'dart:convert';

const String appDisplayName = 'DOXEL';

String newId() => DateTime.now().microsecondsSinceEpoch.toString();

enum Priority { low, normal, urgent }
enum WorkType { school, work, others }
enum AppLanguage { en, id }
enum AppThemeMode { dark, light }
enum UiStyle { simple, compact }
enum PixelFontStyle { visitor, classic }
enum LmsLinkMode { fullUrl, moodleId }
enum LmsActivityType { assign, quiz }

extension PriorityX on Priority {
  int get baseExp {
    switch (this) {
      case Priority.low:
        return 40;
      case Priority.normal:
        return 80;
      case Priority.urgent:
        return 120;
    }
  }

  int get maxDeadlineDays {
    switch (this) {
      case Priority.low:
        return 183;
      case Priority.normal:
        return 62;
      case Priority.urgent:
        return 31;
    }
  }

  int get rank {
    switch (this) {
      case Priority.urgent:
        return 3;
      case Priority.normal:
        return 2;
      case Priority.low:
        return 1;
    }
  }
}

class Quest {
  Quest({
    required this.id,
    required this.title,
    required this.description,
    required this.priority,
    required this.workType,
    required this.createdAt,
    required this.deadline,
    this.favorite = false,
    this.completedAt,
    this.completionNotes = '',
    this.photoPaths = const <String>[],
    this.completionExp = 0,
    this.completedLate = false,
    this.lmsLinkMode = LmsLinkMode.fullUrl,
    this.lmsFullUrl = '',
    this.lmsActivityType = LmsActivityType.assign,
    this.lmsId = '',
  });

  final String id;
  String title;
  String description;
  Priority priority;
  WorkType workType;
  DateTime createdAt;
  DateTime deadline;
  bool favorite;
  DateTime? completedAt;
  String completionNotes;
  List<String> photoPaths;
  int completionExp;
  bool completedLate;
  LmsLinkMode lmsLinkMode;
  String lmsFullUrl;
  LmsActivityType lmsActivityType;
  String lmsId;

  bool get isCompleted => completedAt != null;
  bool get isOverdue => !isCompleted && DateTime.now().isAfter(deadline);

  String get lmsUrl {
    if (lmsLinkMode == LmsLinkMode.fullUrl) return lmsFullUrl.trim();
    final cleanId = lmsId.trim();
    if (cleanId.isEmpty || !RegExp(r'^\d+$').hasMatch(cleanId)) return '';
    final type = lmsActivityType == LmsActivityType.assign ? 'assign' : 'quiz';
    return 'https://mylms.telkomschools.sch.id/mod/$type/view.php?id=$cleanId';
  }

  int expGainAt(DateTime now) {
    if (now.isAfter(deadline)) {
      return (priority.baseExp * 0.5).round();
    }
    final totalHours = deadline.difference(createdAt).inHours.clamp(1, 999999);
    final remainingHours = deadline.difference(now).inHours.clamp(0, totalHours);
    final progress = ((totalHours - remainingHours) / totalHours).clamp(0.0, 1.0);
    return (priority.baseExp * (1 + (progress * 3.0))).round();
  }

  int historyExp() {
    if (completionExp > 0) return completionExp;
    return expGainAt(completedAt ?? DateTime.now());
  }

  bool wasLateCompleted() {
    if (completedLate) return true;
    final doneAt = completedAt;
    return doneAt != null && doneAt.isAfter(deadline);
  }

  bool completedAtLeast24HoursEarly() {
    final doneAt = completedAt;
    return doneAt != null && deadline.difference(doneAt).inHours >= 24;
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'title': title,
        'description': description,
        'priority': priority.name,
        'workType': workType.name,
        'createdAt': createdAt.toIso8601String(),
        'deadline': deadline.toIso8601String(),
        'favorite': favorite,
        'completedAt': completedAt?.toIso8601String(),
        'completionNotes': completionNotes,
        'photoPaths': photoPaths,
        'completionExp': completionExp,
        'completedLate': completedLate,
        'lmsLinkMode': lmsLinkMode.name,
        'lmsFullUrl': lmsFullUrl,
        'lmsActivityType': lmsActivityType.name,
        'lmsId': lmsId,
      };

  factory Quest.fromJson(Map<String, dynamic> json) => Quest(
        id: (json['id'] as String?) ?? newId(),
        title: (json['title'] as String?) ?? '',
        description: (json['description'] as String?) ?? '',
        priority: Priority.values.firstWhere(
          (e) => e.name == json['priority'],
          orElse: () => Priority.normal,
        ),
        workType: WorkType.values.firstWhere(
          (e) => e.name == json['workType'],
          orElse: () => WorkType.school,
        ),
        createdAt: DateTime.tryParse((json['createdAt'] as String?) ?? '') ?? DateTime.now(),
        deadline: DateTime.tryParse((json['deadline'] as String?) ?? '') ?? DateTime.now(),
        favorite: (json['favorite'] as bool?) ?? false,
        completedAt: DateTime.tryParse((json['completedAt'] as String?) ?? ''),
        completionNotes: (json['completionNotes'] as String?) ?? '',
        photoPaths: ((json['photoPaths'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
        completionExp: int.tryParse('${json['completionExp'] ?? 0}') ?? 0,
        completedLate: (json['completedLate'] as bool?) ?? false,
        lmsLinkMode: LmsLinkMode.values.firstWhere(
          (e) => e.name == json['lmsLinkMode'],
          orElse: () => LmsLinkMode.fullUrl,
        ),
        lmsFullUrl: (json['lmsFullUrl'] as String?) ?? '',
        lmsActivityType: LmsActivityType.values.firstWhere(
          (e) => e.name == json['lmsActivityType'],
          orElse: () => LmsActivityType.assign,
        ),
        lmsId: (json['lmsId'] as String?) ?? '',
      );
}

class AppSettings {
  AppSettings({
    this.language = AppLanguage.en,
    this.themeMode = AppThemeMode.dark,
    this.uiStyle = UiStyle.compact,
    this.fontStyle = PixelFontStyle.visitor,
    List<int>? reminderMinutes,
  }) : reminderMinutes = reminderMinutes ?? defaultReminderMinutes;

  AppLanguage language;
  AppThemeMode themeMode;
  UiStyle uiStyle;
  PixelFontStyle fontStyle;
  List<int> reminderMinutes;

  static const List<int> defaultReminderMinutes = <int>[
    21600, // 15 days
    14400, // 10 days
    7200, // 5 days
    4320, // 3 days
    1440, // 1 day
    720, // 12 hours
    360, // 6 hours
    180, // 3 hours
    60, // 1 hour
    30, // 30 minutes
  ];

  Map<String, dynamic> toJson() => <String, dynamic>{
        'language': language.name,
        'themeMode': themeMode.name,
        'uiStyle': uiStyle.name,
        'fontStyle': fontStyle.name,
        'reminderMinutes': reminderMinutes,
      };

  factory AppSettings.fromJson(Map<String, dynamic> json) => AppSettings(
        language: AppLanguage.values.firstWhere(
          (e) => e.name == json['language'],
          orElse: () => AppLanguage.en,
        ),
        themeMode: AppThemeMode.values.firstWhere(
          (e) => e.name == json['themeMode'],
          orElse: () => AppThemeMode.dark,
        ),
        uiStyle: UiStyle.values.firstWhere(
          (e) => e.name == json['uiStyle'],
          orElse: () => UiStyle.compact,
        ),
        fontStyle: PixelFontStyle.values.firstWhere(
          (e) => e.name == json['fontStyle'],
          orElse: () => PixelFontStyle.visitor,
        ),
        reminderMinutes: ((json['reminderMinutes'] as List?) ?? defaultReminderMinutes)
            .map((e) => int.tryParse(e.toString()) ?? 0)
            .where((e) => e > 0)
            .toList(),
      );
}

class AppState {
  AppState({
    this.level = 1,
    this.exp = 0,
    this.streak = 0,
    this.totalCompleted = 0,
    this.lateCompleted = 0,
    this.deadlineFailed = 0,
    this.quests = const <Quest>[],
    this.alertedReminderKeys = const <String>[],
    this.penalizedQuestIds = const <String>[],
    this.unlockedAchievementIds = const <String>[],
  });

  int level;
  int exp;
  int streak;
  int totalCompleted;
  int lateCompleted;
  int deadlineFailed;
  List<Quest> quests;
  List<String> alertedReminderKeys;
  List<String> penalizedQuestIds;
  List<String> unlockedAchievementIds;

  int get expNeeded => 100 + (44 * level);

  int get completedOnTime => totalCompleted - lateCompleted;

  int get completionPercent {
    final totalFinishedOrActive = totalCompleted + quests.where((q) => !q.isCompleted).length;
    if (totalFinishedOrActive <= 0) return 0;
    return ((completedOnTime / totalFinishedOrActive) * 100).clamp(0, 100).round();
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'level': level,
        'exp': exp,
        'streak': streak,
        'totalCompleted': totalCompleted,
        'lateCompleted': lateCompleted,
        'deadlineFailed': deadlineFailed,
        'quests': quests.map((q) => q.toJson()).toList(),
        'alertedReminderKeys': alertedReminderKeys,
        'penalizedQuestIds': penalizedQuestIds,
        'unlockedAchievementIds': unlockedAchievementIds,
      };

  factory AppState.fromJson(Map<String, dynamic> json) => AppState(
        level: int.tryParse('${json['level'] ?? 1}') ?? 1,
        exp: int.tryParse('${json['exp'] ?? 0}') ?? 0,
        streak: int.tryParse('${json['streak'] ?? 0}') ?? 0,
        totalCompleted: int.tryParse('${json['totalCompleted'] ?? 0}') ?? 0,
        lateCompleted: int.tryParse('${json['lateCompleted'] ?? 0}') ?? 0,
        deadlineFailed: int.tryParse('${json['deadlineFailed'] ?? 0}') ?? 0,
        quests: ((json['quests'] as List?) ?? const <dynamic>[])
            .whereType<Map>()
            .map((e) => Quest.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        alertedReminderKeys: ((json['alertedReminderKeys'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
        penalizedQuestIds: ((json['penalizedQuestIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
        unlockedAchievementIds: ((json['unlockedAchievementIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
      );
}

String encodeJson(Object data) => jsonEncode(data);
Map<String, dynamic> decodeJsonMap(String value) => Map<String, dynamic>.from(jsonDecode(value) as Map);
'''


APP_CONTROLLER = r'''
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

class DeadlineAlert {
  DeadlineAlert({required this.title, required this.message});
  final String title;
  final String message;
}

class CompleteResult {
  CompleteResult({required this.expGained, required this.leveledUpTo});
  final int expGained;
  final int? leveledUpTo;
}

enum QuestSortMode { priority, exp }
enum AppNotificationKind { achievement, error, action, deadline, level }

class AppNotification {
  AppNotification({
    required this.kind,
    required this.title,
    required this.message,
    DateTime? occurredAt,
  }) : occurredAt = occurredAt ?? DateTime.now();

  final AppNotificationKind kind;
  final String title;
  final String message;
  final DateTime occurredAt;
}

class AchievementProgress {
  AchievementProgress({
    required this.id,
    required this.title,
    required this.description,
    required this.current,
    required this.goal,
  });

  final String id;
  final String title;
  final String description;
  final int current;
  final int goal;

  int get safeCurrent => current.clamp(0, goal).toInt();
  double get value => goal <= 0 ? 0.0 : (safeCurrent / goal).clamp(0.0, 1.0).toDouble();
  int get percent => (value * 100).round();
  bool get unlocked => safeCurrent >= goal;
}

class AppController extends ChangeNotifier {
  static const _stateKey = 'questclass_v3_state_clean';
  static const _settingsKey = 'questclass_v3_settings';

  AppState state = AppState();
  AppSettings settings = AppSettings();
  QuestSortMode sortMode = QuestSortMode.priority;
  bool ready = false;
  int? levelUpToShow;
  final List<AppNotification> _pendingNotifications = <AppNotification>[];
  final List<DeadlineAlert> _pendingAlerts = <DeadlineAlert>[];
  Timer? _timer;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final rawState = prefs.getString(_stateKey);
    final rawSettings = prefs.getString(_settingsKey);
    if (rawState != null) {
      state = AppState.fromJson(decodeJsonMap(rawState));
    }
    if (rawSettings != null) {
      settings = AppSettings.fromJson(decodeJsonMap(rawSettings));
    }
    ready = true;
    checkDeadlineStatus();
    _syncAchievementUnlocks(notify: false);
    await save();
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(minutes: 1), (_) => checkDeadlineStatus());
    notifyListeners();
  }

  Future<void> save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_stateKey, encodeJson(state.toJson()));
    await prefs.setString(_settingsKey, encodeJson(settings.toJson()));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  List<Quest> activeQuests() {
    final items = state.quests.where((q) => !q.isCompleted).toList();
    items.sort((a, b) {
      if (a.favorite != b.favorite) return a.favorite ? -1 : 1;
      if (sortMode == QuestSortMode.priority) {
        final p = b.priority.rank.compareTo(a.priority.rank);
        if (p != 0) return p;
      } else {
        final e = b.expGainAt(DateTime.now()).compareTo(a.expGainAt(DateTime.now()));
        if (e != 0) return e;
      }
      return a.deadline.compareTo(b.deadline);
    });
    return items;
  }

  List<Quest> completedQuests() {
    final items = state.quests.where((q) => q.isCompleted).toList();
    items.sort((a, b) => (b.completedAt ?? b.deadline).compareTo(a.completedAt ?? a.deadline));
    return items;
  }

  Future<String?> addQuest(Quest quest) async {
    final maxDeadline = quest.createdAt.add(Duration(days: quest.priority.maxDeadlineDays));
    if (quest.deadline.isAfter(maxDeadline)) {
      return 'Deadline too long for this priority. Max ${quest.priority.maxDeadlineDays} days.';
    }
    state.quests.add(quest);
    _pushNotification(
      AppNotification(
        kind: AppNotificationKind.action,
        title: 'ACTION CONFIRMED!',
        message: '${quest.title} was added to your quest list.',
      ),
      shouldNotifyListeners: false,
    );
    await save();
    notifyListeners();
    return null;
  }

  Future<void> toggleFavorite(String questId) async {
    final q = state.quests.where((e) => e.id == questId).firstOrNull;
    if (q == null) return;
    q.favorite = !q.favorite;
    await save();
    notifyListeners();
  }

  Future<CompleteResult?> completeQuest(String questId, {String notes = '', List<String> photoPaths = const <String>[]}) async {
    final q = state.quests.where((e) => e.id == questId).firstOrNull;
    if (q == null || q.isCompleted) return null;
    final now = DateTime.now();
    final late = now.isAfter(q.deadline);
    final gained = q.expGainAt(now);

    q.completedAt = now;
    q.completionNotes = notes;
    q.photoPaths = photoPaths.take(10).toList();
    q.completionExp = gained;
    q.completedLate = late;

    state.exp += gained;
    state.totalCompleted += 1;
    if (late) {
      state.lateCompleted += 1;
      state.streak = 0;
      _pushNotification(
        AppNotification(
          kind: AppNotificationKind.deadline,
          title: 'DEADLINE PASSED!',
          message: '${q.title}: streak reset, but you still gained +$gained EXP.',
        ),
        shouldNotifyListeners: false,
      );
    } else {
      state.streak += 1;
      _pushNotification(
        AppNotification(
          kind: AppNotificationKind.action,
          title: 'ACTION CONFIRMED!',
          message: '${q.title} completed. +$gained EXP gained.',
        ),
        shouldNotifyListeners: false,
      );
    }

    int? levelUp;
    while (state.exp >= state.expNeeded) {
      state.exp -= state.expNeeded;
      state.level += 1;
      levelUp = state.level;
    }
    levelUpToShow = levelUp;
    _syncAchievementUnlocks(notify: true);

    await save();
    notifyListeners();
    return CompleteResult(expGained: gained, leveledUpTo: levelUp);
  }

  Future<void> setSortMode(QuestSortMode mode) async {
    sortMode = mode;
    notifyListeners();
  }

  Future<void> updateSettings(AppSettings next) async {
    settings = next;
    await save();
    notifyListeners();
  }

  Future<void> resetAllData() async {
    state = AppState();
    _pendingNotifications.clear();
    _pendingAlerts.clear();
    levelUpToShow = null;
    await save();
    notifyListeners();
  }

  void notifyError(String title, String message) {
    _pushNotification(AppNotification(kind: AppNotificationKind.error, title: title, message: message));
  }

  void notifyAction(String title, String message) {
    _pushNotification(AppNotification(kind: AppNotificationKind.action, title: title, message: message));
  }

  List<AchievementProgress> achievements(bool Indonesian) {
    final completed = state.totalCompleted;
    final level = state.level;
    final streak = state.streak;
    final missed = state.deadlineFailed + state.lateCompleted;
    final early24 = completedQuests().where((q) => q.completedAtLeast24HoursEarly()).length;
    final withImages = completedQuests().where((q) => q.photoPaths.isNotEmpty).length;
    final withNotes = completedQuests().where((q) => q.completionNotes.trim().isNotEmpty).length;
    final urgentOnTime = completedQuests().where((q) => q.priority == Priority.urgent && !q.wasLateCompleted()).length;

    AchievementProgress a(String id, String title, String desc, int current, int goal) => AchievementProgress(
          id: id,
          title: title,
          description: desc,
          current: current,
          goal: goal,
        );

    return <AchievementProgress>[
      a('quest_1', 'Quest Beginner', 'You completed a quest for the first time!', completed, 1),
      a('quest_5', 'Quest Collector', 'Five quests down. Your todo list is scared.', completed, 5),
      a('quest_10', 'Quest Hunter', 'You completed 10 quests. Not bad, main character.', completed, 10),
      a('quest_25', 'Homework Slayer', '25 quests completed. You are actually grinding.', completed, 25),
      a('quest_50', 'No-Life? Respect.', '50 quests completed. That is kind of insane.', completed, 50),
      a('quest_100', 'Quest Final Boss', '100 quests completed. The checklist fears you.', completed, 100),
      a('level_2', 'GETTING STARTED | LEVEL 2', 'You reached level 2. The tutorial is over.', level, 2),
      a('level_5', "Oh wow, you're intermediate now | LEVEL 5", 'Level 5 reached. Your EXP bar is cooking.', level, 5),
      a('level_10', "Damn, you're a Pro now | LEVEL 10", 'Level 10 reached. Certified quest enjoyer.', level, 10),
      a('level_25', 'Homework Slayer | LEVEL 25', 'Level 25 reached. The grind is getting serious.', level, 25),
      a('level_50', 'Pixel Academic Weapon | LEVEL 50', 'Level 50 reached. Your calendar needs backup.', level, 50),
      a('level_100', 'DOXEL FINAL BOSS | LEVEL 100', 'Level 100 reached. You beat the todo game.', level, 100),
      a('streak_1', 'Streak Spark', 'One clean quest. Keep the flame alive.', streak, 1),
      a('streak_5', 'Streak Keeper', 'Five streak. Now it is becoming a habit.', streak, 5),
      a('streak_10', 'Streak Warrior', 'Ten streak. Deadlines are sweating.', streak, 10),
      a('streak_15', 'Calendar Bully', 'Fifteen streak. You bully your own schedule.', streak, 15),
      a('streak_30', 'Streak Demon', 'Thirty streak. You are locked in.', streak, 30),
      a('streak_60', 'Streak Monster', 'Sixty streak. That is discipline.', streak, 60),
      a('streak_100', 'STREAK GOD!', 'One hundred streak. Absolutely illegal behavior.', streak, 100),
      a('early_24h', 'Early Bird', 'Complete a quest at least 24 hours before deadline.', early24, 1),
      a('miss_streak_1', 'Oops, Streak Gone', 'Lose your streak for the first time.', missed, 1),
      a('miss_deadline_1', 'Huh Loser..', 'Miss a quest deadline for the first time.', missed, 1),
      a('proof_sender', 'Proof Sender', 'Complete a quest with at least one image attached.', withImages, 1),
      a('lore_writer', 'Lore Writer', 'Complete a quest with notes attached.', withNotes, 1),
      a('panic_solver', 'Panic Solver', 'Complete an urgent quest on time.', urgentOnTime, 1),
    ];
  }

  void checkDeadlineStatus() {
    final now = DateTime.now();
    var changed = false;

    for (final q in state.quests.where((q) => !q.isCompleted)) {
      if (now.isAfter(q.deadline) && !state.penalizedQuestIds.contains(q.id)) {
        state.penalizedQuestIds.add(q.id);
        state.deadlineFailed += 1;
        state.streak = 0;
        _pushNotification(
          AppNotification(
            kind: AppNotificationKind.deadline,
            title: 'DEADLINE PASSED!',
            message: '${q.title}: streak reset.',
          ),
          shouldNotifyListeners: false,
        );
        _pendingAlerts.add(DeadlineAlert(title: 'Deadline passed', message: '${q.title}: streak reset.'));
        changed = true;
      }

      if (now.isBefore(q.deadline)) {
        final remainingMinutes = q.deadline.difference(now).inMinutes;
        for (final offset in settings.reminderMinutes) {
          final key = '${q.id}:$offset';
          final shouldAlert = remainingMinutes <= offset && remainingMinutes > offset - 60;
          if (shouldAlert && !state.alertedReminderKeys.contains(key)) {
            state.alertedReminderKeys.add(key);
            _pushNotification(
              AppNotification(
                kind: AppNotificationKind.deadline,
                title: 'DEADLINE SOON!',
                message: '${q.title}: ${_formatRemaining(remainingMinutes)} left.',
              ),
              shouldNotifyListeners: false,
            );
            _pendingAlerts.add(DeadlineAlert(title: 'Deadline soon', message: '${q.title}: ${_formatRemaining(remainingMinutes)} left.'));
            changed = true;
          }
        }
      }
    }

    if (changed) {
      _syncAchievementUnlocks(notify: true);
      save();
      notifyListeners();
    }
  }

  String _formatRemaining(int minutes) {
    if (minutes >= 1440) return '${minutes ~/ 1440} days';
    if (minutes >= 60) return '${minutes ~/ 60} hours';
    return '$minutes minutes';
  }

  void _syncAchievementUnlocks({required bool notify}) {
    var changed = false;
    for (final achievement in achievements(false)) {
      if (achievement.unlocked && !state.unlockedAchievementIds.contains(achievement.id)) {
        state.unlockedAchievementIds.add(achievement.id);
        changed = true;
        if (notify) {
          _pushNotification(
            AppNotification(
              kind: AppNotificationKind.achievement,
              title: 'ACHIEVEMENT OBTAINED!',
              message: '${achievement.title}\n${achievement.description}',
            ),
            shouldNotifyListeners: false,
          );
        }
      }
    }
    if (changed && !notify) {
      save();
    }
  }

  void _pushNotification(AppNotification notification, {bool shouldNotifyListeners = true}) {
    _pendingNotifications.add(notification);
    if (shouldNotifyListeners) notifyListeners();
  }

  List<AppNotification> popPendingNotifications() {
    final out = List<AppNotification>.from(_pendingNotifications);
    _pendingNotifications.clear();
    return out;
  }

  List<DeadlineAlert> popPendingAlerts() {
    final out = List<DeadlineAlert>.from(_pendingAlerts);
    _pendingAlerts.clear();
    return out;
  }

  int? popLevelUp() {
    final out = levelUpToShow;
    levelUpToShow = null;
    return out;
  }
}

extension FirstOrNullExtension<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
'''


MAIN_SHELL = r'''
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
'''


ACHIEVEMENTS_PAGE = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class AchievementsPage extends StatelessWidget {
  const AchievementsPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final items = controller.achievements(l.id);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.achievements),
          for (final a in items)
            Container(
              margin: const EdgeInsets.only(bottom: 14),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: c.panel.withValues(alpha: 0.86),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: a.unlocked ? const Color(0xFFFFC400) : c.line.withValues(alpha: 0.55), width: 2),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Icon(a.unlocked ? Icons.emoji_events : Icons.lock_outline, color: a.unlocked ? const Color(0xFFFFC400) : c.muted),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          a.title,
                          overflow: TextOverflow.ellipsis,
                          maxLines: 2,
                          style: const TextStyle(fontSize: 18, height: 1.05, fontWeight: FontWeight.w900, letterSpacing: 1.3),
                        ),
                      ),
                      if (a.unlocked)
                        Text(l.achievementUnlocked, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFFFFC400))),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(a.description, style: TextStyle(color: c.muted, fontWeight: FontWeight.w800, height: 1.2)),
                  const SizedBox(height: 14),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(99),
                    child: LinearProgressIndicator(
                      minHeight: 10,
                      value: a.value,
                      backgroundColor: c.line.withValues(alpha: 0.12),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: Text('${a.percent}% (${a.safeCurrent}/${a.goal})', style: const TextStyle(fontWeight: FontWeight.w900)),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
'''


GALLERY_PAGE = r'''
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:gallery_saver_plus/gallery_saver.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class GalleryPage extends StatefulWidget {
  const GalleryPage({super.key, required this.controller});
  final AppController controller;

  @override
  State<GalleryPage> createState() => _GalleryPageState();
}

class _GalleryPageState extends State<GalleryPage> {
  final Set<String> _savingQuestIds = <String>{};
  bool _savingAll = false;

  bool get _busy => _savingAll || _savingQuestIds.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final quests = widget.controller.completedQuests().where((q) => q.photoPaths.isNotEmpty).toList();

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.gallery),
          Text(
            'For LMS upload: save the quest images to your phone gallery first, then open LMS, press Choose File, and pick Photos & videos.',
            style: TextStyle(color: c.muted, fontWeight: FontWeight.w900, height: 1.2),
          ),
          const SizedBox(height: 14),
          if (quests.isNotEmpty)
            PixelButton(
              label: _savingAll ? 'SAVING...' : 'SAVE ALL TO PHONE GALLERY',
              filled: true,
              onPressed: _busy ? null : () => _saveAllToGallery(quests),
            ),
          const SizedBox(height: 16),
          if (quests.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in quests) _QuestGalleryCard(
              quest: q,
              saving: _savingQuestIds.contains(q.id),
              onSave: _busy ? null : () => _saveQuestToGallery(q),
              onOpenLms: q.lmsUrl.isEmpty ? null : () => openExternalLink(context, q.lmsUrl),
            ),
        ],
      ),
    );
  }

  Future<void> _saveAllToGallery(List<Quest> quests) async {
    if (_busy) return;
    setState(() => _savingAll = true);
    var saved = 0;
    var total = 0;
    try {
      for (final q in quests) {
        final result = await _savePaths(q.photoPaths);
        saved += result.saved;
        total += result.total;
      }
      if (!mounted) return;
      _showResult(saved, total);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not save images: $e')));
    } finally {
      if (mounted) setState(() => _savingAll = false);
    }
  }

  Future<void> _saveQuestToGallery(Quest quest) async {
    if (_busy) return;
    setState(() => _savingQuestIds.add(quest.id));
    try {
      final result = await _savePaths(quest.photoPaths);
      if (!mounted) return;
      _showResult(result.saved, result.total);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not save images: $e')));
    } finally {
      if (mounted) setState(() => _savingQuestIds.remove(quest.id));
    }
  }

  Future<_GallerySaveResult> _savePaths(List<String> paths) async {
    var saved = 0;
    var total = 0;

    for (final path in paths.take(10)) {
      final file = File(path);
      if (!await file.exists()) continue;
      total += 1;
      final ok = await GallerySaver.saveImage(file.path);
      if (ok == true) saved += 1;
    }

    return _GallerySaveResult(saved: saved, total: total);
  }

  void _showResult(int saved, int total) {
    final message = total == 0
        ? 'No existing image file was found.'
        : 'Saved $saved/$total images. Now open LMS > Choose File > Photos & videos.';
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}

class _GallerySaveResult {
  const _GallerySaveResult({required this.saved, required this.total});
  final int saved;
  final int total;
}

class _QuestGalleryCard extends StatelessWidget {
  const _QuestGalleryCard({
    required this.quest,
    required this.saving,
    required this.onSave,
    required this.onOpenLms,
  });

  final Quest quest;
  final bool saving;
  final VoidCallback? onSave;
  final VoidCallback? onOpenLms;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.85),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: c.line.withValues(alpha: 0.55), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            quest.title.toUpperCase(),
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2),
          ),
          const SizedBox(height: 8),
          Text('Tap image to preview', style: TextStyle(color: c.muted, fontSize: 12, fontWeight: FontWeight.w900)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              for (int i = 0; i < quest.photoPaths.length; i++)
                InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => showGalleryImagePreview(context, quest.photoPaths, i),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(
                      File(quest.photoPaths[i]),
                      width: 92,
                      height: 92,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        width: 92,
                        height: 92,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: c.line, width: 2),
                        ),
                        child: const Icon(Icons.broken_image),
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              Expanded(
                child: PixelButton(
                  label: saving ? 'SAVING...' : 'SAVE TO GALLERY',
                  filled: true,
                  onPressed: onSave,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: PixelButton(
                  label: 'OPEN LMS',
                  filled: false,
                  onPressed: onOpenLms,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

Future<void> showGalleryImagePreview(BuildContext context, List<String> paths, int initialIndex) async {
  if (paths.isEmpty) return;
  final safeInitial = initialIndex.clamp(0, paths.length - 1).toInt();
  await showDialog<void>(
    context: context,
    barrierColor: Colors.black87,
    builder: (_) => _GalleryImagePreviewDialog(paths: List<String>.from(paths), initialIndex: safeInitial),
  );
}

class _GalleryImagePreviewDialog extends StatefulWidget {
  const _GalleryImagePreviewDialog({required this.paths, required this.initialIndex});
  final List<String> paths;
  final int initialIndex;

  @override
  State<_GalleryImagePreviewDialog> createState() => _GalleryImagePreviewDialogState();
}

class _GalleryImagePreviewDialogState extends State<_GalleryImagePreviewDialog> {
  late final PageController _pageController;
  late int index;

  @override
  void initState() {
    super.initState();
    index = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black,
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            PageView.builder(
              controller: _pageController,
              itemCount: widget.paths.length,
              onPageChanged: (value) => setState(() => index = value),
              itemBuilder: (_, i) {
                final path = widget.paths[i];
                return InteractiveViewer(
                  minScale: 0.6,
                  maxScale: 5,
                  child: Center(
                    child: Image.file(
                      File(path),
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, color: Colors.white, size: 64),
                    ),
                  ),
                );
              },
            ),
            Positioned(
              top: 8,
              right: 8,
              child: IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close, color: Colors.white, size: 32),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 18,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(99)),
                  child: Text('${index + 1}/${widget.paths.length}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
'''


def patch_app_title_and_label() -> None:
    # MaterialApp title
    app = SRC / "app.dart"
    if app.exists():
        text = read(app)
        text = re.sub(r"title:\s*'[^']*'", "title: 'Doxel'", text, count=1)
        write(app, text)

    # Android app label, if present.
    manifest = ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest.exists():
        text = read(manifest)
        if 'android:label=' in text:
            text = re.sub(r'android:label="[^"]*"', 'android:label="Doxel"', text, count=1)
            write(manifest, text)


def patch_i18n_small_texts() -> None:
    path = SRC / "i18n.dart"
    if not path.exists():
        return
    text = read(path)
    text = text.replace("Favorite + highest priority", "Highest priority")
    text = text.replace("Favorite + highest EXP", "Highest EXP")
    text = text.replace("Favorit + prioritas tertinggi", "Prioritas tertinggi")
    text = text.replace("Favorit + EXP tertinggi", "EXP tertinggi")
    write(path, text)


def patch_create_sheet_errors_to_overlay() -> None:
    path = SRC / "create_quest_sheet.dart"
    if not path.exists():
        return
    text = read(path)
    pattern = r"void showError\(String message\) \{\s*ScaffoldMessenger\.of\(context\)\.showSnackBar\(SnackBar\(content: Text\(message\)\)\);\s*\}"
    replacement = """void showError(String message) {
      widget.controller.notifyError('ERROR OCCURRED!', message);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }"""
    new_text = re.sub(pattern, replacement, text, count=1, flags=re.S)
    if new_text != text:
      write(path, new_text)
    else:
      print("warning: could not patch create_quest_sheet.dart showError, leaving SnackBar errors as-is")


def main() -> None:
    ensure_dependency('gallery_saver_plus', '3.2.9')
    write(SRC / "models.dart", MODELS)
    write(SRC / "app_controller.dart", APP_CONTROLLER)
    write(SRC / "main_shell.dart", MAIN_SHELL)
    write(SRC / "achievements_page.dart", ACHIEVEMENTS_PAGE)
    write(SRC / "gallery_page.dart", GALLERY_PAGE)
    patch_i18n_small_texts()
    patch_app_title_and_label()
    patch_create_sheet_errors_to_overlay()

    print("""
DONE v9.

Now run:
  flutter clean
  flutter pub get
  flutter run

Changes:
- App name changed to DOXEL / Doxel.
- Gallery images can now be tapped and previewed fullscreen with zoom/swipe.
- Added animated overlay notifications at the top of the app.
- Quest created/completed, deadline alerts, level up, and new achievements now use the overlay style.
- Form errors will try to use the overlay too; SnackBar remains as fallback.
- Added funny achievement sets for quest count, level, streak, and misc actions.
- Existing unlocked achievements are marked silently on first load after this patch, so old progress does not spam you with many popups.
""")


if __name__ == "__main__":
    main()
