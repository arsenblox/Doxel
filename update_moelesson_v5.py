from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
LIB = ROOT / "lib"
SRC = LIB / "src"
APP_NAME = "PIXDO"  # Pixel + ToDo. Change this if you want another display name.

if not (ROOT / "pubspec.yaml").exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")
if not SRC.exists():
    raise SystemExit("Could not find lib/src. Run this inside your current Flutter project.")


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_v5")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path: Path, text: str) -> None:
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("patched", path.relative_to(ROOT))


models = r'''
import 'dart:convert';

const String appDisplayName = 'PIXDO';

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
      };

  factory AppState.fromJson(Map<String, dynamic> json) => AppState(
        level: (json['level'] as int?) ?? 1,
        exp: (json['exp'] as int?) ?? 0,
        streak: (json['streak'] as int?) ?? 0,
        totalCompleted: (json['totalCompleted'] as int?) ?? 0,
        lateCompleted: (json['lateCompleted'] as int?) ?? 0,
        deadlineFailed: (json['deadlineFailed'] as int?) ?? 0,
        quests: ((json['quests'] as List?) ?? const <dynamic>[])
            .whereType<Map>()
            .map((e) => Quest.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        alertedReminderKeys: ((json['alertedReminderKeys'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
        penalizedQuestIds: ((json['penalizedQuestIds'] as List?) ?? const <dynamic>[]).map((e) => e.toString()).toList(),
      );
}

String encodeJson(Object data) => jsonEncode(data);
Map<String, dynamic> decodeJsonMap(String value) => Map<String, dynamic>.from(jsonDecode(value) as Map);
'''.replace("const String appDisplayName = 'PIXDO';", f"const String appDisplayName = '{APP_NAME}';")


i18n = r'''
import 'models.dart';

class L10n {
  L10n(this.language);
  final AppLanguage language;
  bool get id => language == AppLanguage.id;

  String get appName => appDisplayName;
  String get stats => id ? 'STATISTIK' : 'STATS';
  String get calendar => id ? 'KALENDER' : 'CALENDAR';
  String get homework => id ? 'TUGAS' : 'HOMEWORK';
  String get history => id ? 'RIWAYAT' : 'HISTORY';
  String get gallery => id ? 'GALERI' : 'GALLERY';
  String get achievements => id ? 'ACHIEVEMENT' : 'ACHIEVEMENTS';
  String get settings => id ? 'PENGATURAN' : 'SETTINGS';
  String get completed => id ? 'SELESAI' : 'COMPLETED';
  String get late => id ? 'TELAT' : 'LATE';
  String get due => id ? 'DEADLINE' : 'ON DUE';
  String get streak => id ? 'STREAK' : 'STREAK';
  String get level => id ? 'LEVEL' : 'LEVEL';
  String get complete => id ? 'SELESAI' : 'COMPLETE';
  String get moreInfo => id ? 'DETAIL' : 'MORE INFO';
  String get createQuest => id ? 'BUAT QUEST' : 'CREATE QUEST';
  String get title => id ? 'Nama' : 'Name';
  String get description => id ? 'Deskripsi' : 'Description';
  String get priority => id ? 'Prioritas' : 'Priority';
  String get typeOfWork => id ? 'Tipe tugas' : 'Type of work';
  String get deadline => id ? 'Deadline' : 'Deadline';
  String get link => id ? 'Link LMS' : 'LMS Link';
  String get fullUrl => id ? 'URL penuh' : 'Full URL';
  String get lmsId => id ? 'ID LMS' : 'LMS ID';
  String get notesOptional => id ? 'Catatan opsional' : 'Optional notes';
  String get photosOptional => id ? 'Foto opsional, maksimal 10' : 'Optional photos, max 10';
  String get save => id ? 'Simpan' : 'Save';
  String get cancel => id ? 'Batal' : 'Cancel';
  String get noQuest => id ? 'Belum ada quest.' : 'No quests yet.';
  String get sort => id ? 'Urutkan' : 'Sort';
  String get sortPriority => id ? 'Favorit + prioritas tertinggi' : 'Favorite + highest priority';
  String get sortExp => id ? 'Favorit + EXP tertinggi' : 'Favorite + highest EXP';
  String get openLms => id ? 'Buka LMS' : 'Open LMS';
  String get favorite => id ? 'Favorit' : 'Favorite';
  String get resetData => id ? 'Reset semua data' : 'Reset all data';
  String get uiDesign => id ? 'Desain UI' : 'UI Design';
  String get compact => id ? 'Compact / seperti desain' : 'Compact / like design';
  String get simple => id ? 'Simple' : 'Simple';
  String get language => id ? 'Bahasa' : 'Language';
  String get theme => id ? 'Tema' : 'Theme';
  String get font => id ? 'Font' : 'Font';
  String get reminders => id ? 'Pengingat deadline' : 'Deadline reminders';
  String get levelUp => id ? 'LEVEL NAIK!' : 'LEVEL UP!';
  String get deadlinePassed => id ? 'Deadline lewat. Streak hilang.' : 'Deadline passed. Streak lost.';
  String get dueSoon => id ? 'Deadline segera datang' : 'Deadline soon';
  String get expGained => id ? 'EXP didapat' : 'EXP gained';
  String get completedLate => id ? 'SELESAI TELAT' : 'COMPLETED LATE';
  String get completedOnTime => id ? 'SELESAI TEPAT WAKTU' : 'COMPLETED ON TIME';
  String get achievementUnlocked => id ? 'TERBUKA' : 'UNLOCKED';

  String scoreLabel(int percent) {
    if (percent == 100) return id ? 'LUAR BIASA!' : 'AWESOME!';
    if (percent > 85) return id ? 'SANGAT BAIK!' : 'VERY GOOD!';
    if (percent > 65) return id ? 'BAIK!' : 'GOOD!';
    if (percent > 50) return id ? 'LUMAYAN.' : 'NOT BAD.';
    if (percent > 35) return id ? 'COBA LAGI..' : "LET'S TRY AGAIN..";
    if (percent > 15) return id ? 'TETAP MAJU!' : 'KEEP GOING!';
    return id ? 'MULAI SEKARANG!' : 'START NOW!';
  }

  String monthName(int month) {
    const en = <String>['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const ind = <String>['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    final list = id ? ind : en;
    return list[(month - 1).clamp(0, 11).toInt()];
  }

  String priorityName(Priority p) {
    switch (p) {
      case Priority.low:
        return id ? 'RENDAH' : 'LOW';
      case Priority.normal:
        return id ? 'NORMAL' : 'NORMAL';
      case Priority.urgent:
        return id ? 'DARURAT' : 'URGENT';
    }
  }

  String workTypeName(WorkType t) {
    switch (t) {
      case WorkType.school:
        return id ? 'Sekolah' : 'School';
      case WorkType.work:
        return id ? 'Kerja' : 'Work';
      case WorkType.others:
        return id ? 'Lainnya' : 'Others';
    }
  }

  String reminderLabel(int minutes) {
    if (minutes >= 1440) {
      final days = minutes ~/ 1440;
      return id ? '$days hari sebelum deadline' : '$days days until deadline';
    }
    if (minutes >= 60) {
      final hours = minutes ~/ 60;
      return id ? '$hours jam sebelum deadline' : '$hours hours until deadline';
    }
    return id ? '$minutes menit sebelum deadline' : '$minutes minutes until deadline';
  }
}
'''


app_controller = r'''
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

class AchievementProgress {
  AchievementProgress({required this.title, required this.description, required this.current, required this.goal});
  final String title;
  final String description;
  final int current;
  final int goal;

  int get safeCurrent => current.clamp(0, goal).toInt();
  double get value => goal <= 0 ? 0.0 : (safeCurrent / goal).clamp(0.0, 1.0).toDouble();
  int get percent => (value * 100).round();
  bool get unlocked => safeCurrent >= goal;
}

enum QuestSortMode { priority, exp }

class AppController extends ChangeNotifier {
  static const _stateKey = 'questclass_v3_state_clean';
  static const _settingsKey = 'questclass_v3_settings';

  AppState state = AppState();
  AppSettings settings = AppSettings();
  QuestSortMode sortMode = QuestSortMode.priority;
  bool ready = false;
  int? levelUpToShow;
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
      _pendingAlerts.add(DeadlineAlert(title: 'Deadline passed', message: '${q.title}: streak reset.'));
    } else {
      state.streak += 1;
    }

    int? levelUp;
    while (state.exp >= state.expNeeded) {
      state.exp -= state.expNeeded;
      state.level += 1;
      levelUp = state.level;
    }
    levelUpToShow = levelUp;

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
    await save();
    notifyListeners();
  }

  List<AchievementProgress> achievements(bool Indonesian) {
    final completed = state.totalCompleted;
    final level = state.level;
    return <AchievementProgress>[
      AchievementProgress(
        title: Indonesian ? 'Quest Beginner' : 'Quest Beginner',
        description: Indonesian ? 'Kamu menyelesaikan quest untuk pertama kali!' : 'You completed quest for the first time!',
        current: completed,
        goal: 1,
      ),
      AchievementProgress(
        title: Indonesian ? 'Quest Rookie' : 'Quest Rookie',
        description: Indonesian ? 'Selesaikan 5 quest.' : 'Complete 5 quests.',
        current: completed,
        goal: 5,
      ),
      AchievementProgress(
        title: Indonesian ? 'Quest Hunter' : 'Quest Hunter',
        description: Indonesian ? 'Selesaikan 10 quest.' : 'Complete 10 quests.',
        current: completed,
        goal: 10,
      ),
      AchievementProgress(
        title: Indonesian ? 'Level Awakened' : 'Level Awakened',
        description: Indonesian ? 'Capai level 2.' : 'Reach level 2.',
        current: level,
        goal: 2,
      ),
      AchievementProgress(
        title: Indonesian ? 'Level Grinder' : 'Level Grinder',
        description: Indonesian ? 'Capai level 5.' : 'Reach level 5.',
        current: level,
        goal: 5,
      ),
      AchievementProgress(
        title: Indonesian ? 'Pixel Legend' : 'Pixel Legend',
        description: Indonesian ? 'Capai level 10.' : 'Reach level 10.',
        current: level,
        goal: 10,
      ),
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
            _pendingAlerts.add(DeadlineAlert(title: 'Deadline soon', message: '${q.title}: ${_formatRemaining(remainingMinutes)} left.'));
            changed = true;
          }
        }
      }
    }

    if (changed) {
      save();
      notifyListeners();
    }
  }

  String _formatRemaining(int minutes) {
    if (minutes >= 1440) return '${minutes ~/ 1440} days';
    if (minutes >= 60) return '${minutes ~/ 60} hours';
    return '$minutes minutes';
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


pixel_widgets = r'''
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'app_theme.dart';

class PixelPanel extends StatelessWidget {
  const PixelPanel({
    super.key,
    required this.child,
    this.title,
    this.padding = const EdgeInsets.all(18),
    this.height,
    this.margin,
  });

  final Widget child;
  final String? title;
  final EdgeInsets padding;
  final double? height;
  final EdgeInsets? margin;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Container(
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.88),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: c.line.withValues(alpha: 0.55), width: 2),
        boxShadow: <BoxShadow>[
          BoxShadow(color: Colors.black.withValues(alpha: 0.18), blurRadius: 18, offset: const Offset(0, 12)),
        ],
      ),
      child: Padding(
        padding: padding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            if (title != null) ...<Widget>[
              Center(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    title!,
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    style: TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2, color: c.text),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Center(child: Container(width: 250, height: 2, color: c.line.withValues(alpha: 0.82))),
              const SizedBox(height: 14),
            ],
            Expanded(child: child),
          ],
        ),
      ),
    );
  }
}

/// Kept as a harmless empty widget so older files that still reference it will not break.
class PixelCorners extends StatelessWidget {
  const PixelCorners({super.key, required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Column(
        children: <Widget>[
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(text, maxLines: 1, style: TextStyle(fontSize: 23, height: 1.0, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 3)),
          ),
          const SizedBox(height: 8),
          Container(width: 650, height: 4, color: c.line.withValues(alpha: 0.88)),
        ],
      ),
    );
  }
}

class DonutChart extends StatelessWidget {
  const DonutChart({super.key, required this.completed, required this.late, required this.onDue, required this.percent});
  final int completed;
  final int late;
  final int onDue;
  final int percent;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _DonutPainter(completed: completed, late: late, onDue: onDue),
      child: Center(
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Text('$percent%', style: const TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, color: Colors.white)),
        ),
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  _DonutPainter({required this.completed, required this.late, required this.onDue});
  final int completed;
  final int late;
  final int onDue;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final stroke = math.max(20.0, size.shortestSide * 0.22);
    final total = math.max(1, completed + late + onDue);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.butt;
    double start = -math.pi / 2;
    void arc(int value, Color color) {
      final sweep = (value / total) * math.pi * 2;
      paint.color = color;
      canvas.drawArc(rect.deflate(stroke / 2), start, sweep, false, paint);
      start += sweep;
    }
    arc(completed <= 0 && late <= 0 && onDue <= 0 ? 1 : completed, const Color(0xFF00FF39));
    if (late > 0) arc(late, const Color(0xFFFF1208));
    if (onDue > 0) arc(onDue, const Color(0xFFFFC400));
  }

  @override
  bool shouldRepaint(covariant _DonutPainter oldDelegate) => true;
}

class PixelButton extends StatelessWidget {
  const PixelButton({super.key, required this.label, required this.onPressed, this.filled = false, this.icon});
  final String label;
  final VoidCallback? onPressed;
  final bool filled;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: icon == null ? const SizedBox.shrink() : Icon(icon, size: 18),
      label: FittedBox(fit: BoxFit.scaleDown, child: Text(label, maxLines: 1, style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5))),
      style: OutlinedButton.styleFrom(
        foregroundColor: filled ? c.panel : c.text,
        backgroundColor: filled ? c.line : Colors.transparent,
        side: BorderSide(color: c.line, width: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
      ),
    );
  }
}
'''


stats_card = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class StatsCard extends StatelessWidget {
  const StatsCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final s = controller.state;
    final active = controller.state.quests.where((q) => !q.isCompleted).length;
    final width = MediaQuery.sizeOf(context).width;
    final height = width < 430 ? 250.0 : 285.0;
    return PixelPanel(
      title: l.stats,
      height: height,
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 18),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final donutSize = (constraints.maxWidth * 0.32).clamp(96.0, 170.0);
          return Row(
            children: <Widget>[
              SizedBox(
                width: donutSize,
                height: donutSize,
                child: DonutChart(
                  completed: s.completedOnTime,
                  late: s.lateCompleted,
                  onDue: active,
                  percent: s.completionPercent,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    FittedBox(
                      alignment: Alignment.centerLeft,
                      fit: BoxFit.scaleDown,
                      child: Text(l.scoreLabel(s.completionPercent), maxLines: 1, style: const TextStyle(fontSize: 38, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 3)),
                    ),
                    const SizedBox(height: 14),
                    _bar(context),
                    const SizedBox(height: 12),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(flex: 12, child: _legend(context, l, active)),
                        Expanded(flex: 9, child: _miniStat(context, l.streak, '${s.streak}')),
                        Expanded(flex: 12, child: _miniStat(context, l.level, '${s.level}\n${s.exp}/${s.expNeeded}')),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _bar(BuildContext context) {
    final c = appColors(context);
    final pct = controller.state.expNeeded == 0 ? 0.0 : (controller.state.exp / controller.state.expNeeded).clamp(0.0, 1.0);
    return Column(
      children: <Widget>[
        Container(height: 5, color: c.line.withValues(alpha: 0.9)),
        const SizedBox(height: 5),
        Align(
          alignment: Alignment.centerLeft,
          child: FractionallySizedBox(widthFactor: pct, child: Container(height: 5, color: c.line.withValues(alpha: 0.6))),
        ),
      ],
    );
  }

  Widget _legend(BuildContext context, L10n l, int active) {
    final c = appColors(context);
    Widget item(Color color, String text) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(children: <Widget>[
            Container(width: 12, height: 12, color: color),
            const SizedBox(width: 6),
            Expanded(child: Text(text, overflow: TextOverflow.ellipsis, maxLines: 1, style: TextStyle(color: c.text, fontSize: 11, height: 1.0, fontWeight: FontWeight.w900))),
          ]),
        );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        item(const Color(0xFF00FF39), l.completed),
        item(const Color(0xFFFF1208), l.late),
        item(const Color(0xFFFFC400), l.due),
      ],
    );
  }

  Widget _miniStat(BuildContext context, String title, String value) {
    final c = appColors(context);
    return Padding(
      padding: const EdgeInsets.only(left: 6),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          SizedBox(
            height: 18,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(title, maxLines: 1, textAlign: TextAlign.center, style: TextStyle(fontSize: 14, height: 1.0, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 1.6)),
            ),
          ),
          Container(height: 2, color: c.line.withValues(alpha: 0.85)),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(value, textAlign: TextAlign.center, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: c.text, height: 1.1)),
          ),
        ],
      ),
    );
  }
}
'''


calendar_card = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class CalendarCard extends StatefulWidget {
  const CalendarCard({super.key, required this.controller});
  final AppController controller;

  @override
  State<CalendarCard> createState() => _CalendarCardState();
}

class _CalendarCardState extends State<CalendarCard> {
  late DateTime month;
  DateTime? selected;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    month = DateTime(now.year, now.month);
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    final days = DateUtils.getDaysInMonth(month.year, month.month);
    final firstWeekday = DateTime(month.year, month.month, 1).weekday; // Mon=1
    final active = widget.controller.activeQuests();
    final selectedTasks = selected == null
        ? <dynamic>[]
        : active.where((q) => DateUtils.isSameDay(q.deadline, selected)).toList();

    return PixelPanel(
      title: l.calendar,
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final tiny = constraints.maxHeight < 300 || constraints.maxWidth < 320;
          final cells = List<Widget>.generate(42, (i) {
            final day = i - (firstWeekday - 1) + 1;
            if (day < 1 || day > days) return const SizedBox.shrink();
            final date = DateTime(month.year, month.month, day);
            final count = active.where((q) => DateUtils.isSameDay(q.deadline, date)).length;
            final isToday = DateUtils.isSameDay(date, DateTime.now());
            final isSelected = selected != null && DateUtils.isSameDay(date, selected);
            return InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: () => setState(() => selected = date),
              child: Container(
                padding: EdgeInsets.all(tiny ? 1 : 2),
                decoration: BoxDecoration(
                  color: isSelected ? c.line.withValues(alpha: 0.18) : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  border: isToday ? Border.all(color: c.accent, width: 2) : null,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Flexible(
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text('$day', maxLines: 1, style: TextStyle(fontSize: tiny ? 10 : 13, height: 1.0, fontWeight: FontWeight.w900, color: c.text)),
                      ),
                    ),
                    SizedBox(height: tiny ? 1 : 2),
                    if (count > 0)
                      Container(width: tiny ? 4 : 6, height: tiny ? 4 : 6, decoration: const BoxDecoration(color: Color(0xFFFFC400), shape: BoxShape.circle))
                    else
                      SizedBox(height: tiny ? 4 : 6),
                  ],
                ),
              ),
            );
          });

          return Column(
            children: <Widget>[
              SizedBox(
                height: tiny ? 32 : 40,
                child: Row(
                  children: <Widget>[
                    IconButton(padding: EdgeInsets.zero, onPressed: () => setState(() => month = DateTime(month.year, month.month - 1)), icon: const Icon(Icons.chevron_left)),
                    Expanded(
                      child: Center(
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Text('${l.monthName(month.month)} ${month.year}', maxLines: 1, style: const TextStyle(fontSize: 18, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 1.8)),
                        ),
                      ),
                    ),
                    IconButton(padding: EdgeInsets.zero, onPressed: () => setState(() => month = DateTime(month.year, month.month + 1)), icon: const Icon(Icons.chevron_right)),
                  ],
                ),
              ),
              SizedBox(
                height: tiny ? 18 : 22,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: const <Widget>[
                    _Week('M'), _Week('T'), _Week('W'), _Week('T'), _Week('F'), _Week('S'), _Week('S'),
                  ],
                ),
              ),
              const SizedBox(height: 4),
              Expanded(
                child: GridView.count(
                  padding: EdgeInsets.zero,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 7,
                  childAspectRatio: tiny ? 1.0 : 1.08,
                  mainAxisSpacing: tiny ? 1 : 2,
                  crossAxisSpacing: tiny ? 1 : 2,
                  children: cells,
                ),
              ),
              if (!tiny && selectedTasks.isNotEmpty)
                SizedBox(
                  height: 36,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: selectedTasks.map<Widget>((q) => Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: Chip(label: Text(q.title, overflow: TextOverflow.ellipsis)),
                        )).toList(),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _Week extends StatelessWidget {
  const _Week(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Expanded(child: Center(child: Text(text, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, height: 1.0))));
}
'''


home_page = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'calendar_card.dart';
import 'create_quest_sheet.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';
import 'quest_card.dart';
import 'stats_card.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final compact = controller.settings.uiStyle == UiStyle.compact;
    final quests = controller.activeQuests();
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: SizedBox(
        width: 54,
        height: 54,
        child: FloatingActionButton(
          heroTag: 'createQuest',
          onPressed: () => showCreateQuestSheet(context, controller),
          child: const Icon(Icons.add, size: 28),
        ),
      ),
      body: CustomScrollView(
        slivers: <Widget>[
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
            sliver: SliverList(
              delegate: SliverChildListDelegate(<Widget>[
                StatsCard(controller: controller),
                const SizedBox(height: 22),
                SizedBox(height: compact ? 345 : 410, child: CalendarCard(controller: controller)),
                SectionTitle(l.homework),
                Row(
                  children: <Widget>[
                    Text(l.sort, style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButton<QuestSortMode>(
                        isExpanded: true,
                        value: controller.sortMode,
                        items: <DropdownMenuItem<QuestSortMode>>[
                          DropdownMenuItem(value: QuestSortMode.priority, child: Text(l.sortPriority)),
                          DropdownMenuItem(value: QuestSortMode.exp, child: Text(l.sortExp)),
                        ],
                        onChanged: (v) => v == null ? null : controller.setSortMode(v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (quests.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 40),
                    child: Center(child: Text(l.noQuest, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18))),
                  )
                else
                  for (final q in quests) QuestCard(controller: controller, quest: q),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}
'''


quest_card = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'complete_quest_sheet.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class QuestCard extends StatelessWidget {
  const QuestCard({super.key, required this.controller, required this.quest, this.compact = false});
  final AppController controller;
  final Quest quest;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final pName = l.priorityName(quest.priority);
    final exp = quest.expGainAt(DateTime.now());
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: EdgeInsets.all(compact ? 12 : 18),
      decoration: BoxDecoration(
        color: c.panel.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(compact ? 12 : 28),
        border: Border.all(color: c.line.withValues(alpha: 0.8), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(quest.title.toUpperCase(), overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 13 : 21, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2)),
              ),
              IconButton(
                tooltip: l.favorite,
                onPressed: () => controller.toggleFavorite(quest.id),
                icon: Icon(quest.favorite ? Icons.star : Icons.star_border, color: quest.favorite ? const Color(0xFFFFC400) : c.text),
              ),
            ],
          ),
          Container(height: 2, color: c.line.withValues(alpha: 0.85)),
          const SizedBox(height: 8),
          if (!compact && quest.description.trim().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Text(quest.description.toUpperCase(), maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 16, color: c.muted, fontWeight: FontWeight.w900, letterSpacing: 1.3)),
            ),
          Wrap(
            spacing: 14,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: <Widget>[
              Text('${l.priority}: ', style: TextStyle(color: c.muted, fontWeight: FontWeight.w900)),
              Text(pName, style: TextStyle(color: priorityColor(pName, context), fontWeight: FontWeight.w900, letterSpacing: 1.4)),
              Text('EXP $exp', style: TextStyle(color: c.text, fontWeight: FontWeight.w900)),
              Text('${l.deadline}: ${formatDateTime(quest.deadline)}', style: TextStyle(color: c.text, fontWeight: FontWeight.w900)),
              Text(remainingText(quest.deadline), style: TextStyle(color: quest.isOverdue ? const Color(0xFFFF4C67) : c.accent, fontWeight: FontWeight.w900)),
            ],
          ),
          if (!compact) const SizedBox(height: 16),
          if (!compact)
            Row(
              children: <Widget>[
                if (quest.lmsUrl.isNotEmpty)
                  Expanded(child: PixelButton(label: l.openLms, icon: Icons.open_in_new, onPressed: () => openExternalLink(context, quest.lmsUrl))),
                if (quest.lmsUrl.isNotEmpty) const SizedBox(width: 12),
                Expanded(
                  child: PixelButton(
                    label: l.complete,
                    filled: true,
                    onPressed: () => showCompleteQuestSheet(context, controller, quest),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

// This is kept only for backward compatibility with older code. The home screen no longer uses ON DUE.
class OnDueCard extends StatelessWidget {
  const OnDueCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
'''


history_page = r'''
import 'dart:io';

import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final items = controller.completedQuests();
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.history),
          if (items.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in items)
              Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: c.panel.withValues(alpha: 0.85), borderRadius: BorderRadius.circular(24), border: Border.all(color: c.line.withValues(alpha: 0.6), width: 2)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(child: Text(q.title.toUpperCase(), overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 22, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 2))),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(color: q.wasLateCompleted() ? const Color(0xFFFF4C67).withValues(alpha: 0.18) : const Color(0xFF00FF39).withValues(alpha: 0.15), borderRadius: BorderRadius.circular(99)),
                          child: Text(q.wasLateCompleted() ? l.completedLate : l.completedOnTime, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: q.wasLateCompleted() ? const Color(0xFFFF4C67) : const Color(0xFF00FF39))),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('${l.completed}: ${formatDateTime(q.completedAt ?? q.deadline)}'),
                    const SizedBox(height: 4),
                    Text('${l.expGained}: +${q.historyExp()} EXP', style: const TextStyle(fontWeight: FontWeight.w900)),
                    if (q.completionNotes.trim().isNotEmpty) ...<Widget>[
                      const SizedBox(height: 10),
                      Text(q.completionNotes),
                    ],
                    if (q.photoPaths.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 12),
                      SizedBox(
                        height: 86,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          itemBuilder: (_, i) => ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.file(File(q.photoPaths[i]), width: 86, height: 86, fit: BoxFit.cover)),
                          separatorBuilder: (_, __) => const SizedBox(width: 8),
                          itemCount: q.photoPaths.length,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
        ],
      ),
    );
  }
}
'''


achievements_page = r'''
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
                      Expanded(child: Text(a.title, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 20, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 1.6))),
                      if (a.unlocked)
                        Text(l.achievementUnlocked, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFFFFC400))),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(a.description, style: TextStyle(color: c.muted, fontWeight: FontWeight.w800)),
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


main_shell = r'''
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

class _MainShellState extends State<MainShell> with SingleTickerProviderStateMixin {
  int index = 0;
  bool showingAlert = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onController);
    WidgetsBinding.instance.addPostFrameCallback((_) => _onController());
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onController);
    super.dispose();
  }

  void _onController() {
    if (!mounted || showingAlert) return;
    final level = widget.controller.popLevelUp();
    if (level != null) {
      showingAlert = true;
      showDialog<void>(context: context, builder: (_) => LevelUpDialog(level: level)).then((_) => showingAlert = false);
      return;
    }
    final alerts = widget.controller.popPendingAlerts();
    if (alerts.isNotEmpty) {
      showingAlert = true;
      showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(alerts.first.title),
          content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: alerts.map((a) => Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(a.message))).toList()),
          actions: <Widget>[TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
        ),
      ).then((_) => showingAlert = false);
    }
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
        child: Scaffold(
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
                        child: Text(l.appName, maxLines: 1, style: const TextStyle(fontSize: 42, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 4)),
                      ),
                    ),
                    IconButton(iconSize: 30, onPressed: () {}, icon: const Icon(Icons.notifications)),
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
            margin: const EdgeInsets.fromLTRB(0, 0, 0, 0),
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
      ),
    );
  }
}

class LevelUpDialog extends StatefulWidget {
  const LevelUpDialog({super.key, required this.level});
  final int level;

  @override
  State<LevelUpDialog> createState() => _LevelUpDialogState();
}

class _LevelUpDialogState extends State<LevelUpDialog> with SingleTickerProviderStateMixin {
  late final AnimationController controller;
  late final Animation<double> scale;
  late final Animation<double> turns;

  @override
  void initState() {
    super.initState();
    controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 850))..forward();
    scale = CurvedAnimation(parent: controller, curve: Curves.elasticOut);
    turns = Tween<double>(begin: -0.03, end: 0.03).animate(CurvedAnimation(parent: controller, curve: Curves.easeInOutBack));
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = appColors(context);
    return Dialog(
      backgroundColor: Colors.transparent,
      child: ScaleTransition(
        scale: scale,
        child: RotationTransition(
          turns: turns,
          child: Container(
            padding: const EdgeInsets.all(26),
            decoration: BoxDecoration(
              color: c.panel,
              borderRadius: BorderRadius.circular(30),
              border: Border.all(color: const Color(0xFFFFC400), width: 3),
              boxShadow: <BoxShadow>[BoxShadow(color: const Color(0xFFFFC400).withValues(alpha: 0.25), blurRadius: 34, spreadRadius: 8)],
            ),
            child: Column(mainAxisSize: MainAxisSize.min, children: <Widget>[
              const Icon(Icons.auto_awesome, size: 76, color: Color(0xFFFFC400)),
              const SizedBox(height: 10),
              const FittedBox(child: Text('LEVEL UP!', style: TextStyle(fontSize: 32, height: 1.0, fontWeight: FontWeight.w900, letterSpacing: 3))),
              const SizedBox(height: 8),
              Text('LEVEL ${widget.level}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
              const SizedBox(height: 18),
              FilledButton(onPressed: () => Navigator.pop(context), child: const Text('OK')),
            ]),
          ),
        ),
      ),
    );
  }
}
'''


app_dart = r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'main_shell.dart';
import 'models.dart';

class QuestClassApp extends StatefulWidget {
  const QuestClassApp({super.key});

  @override
  State<QuestClassApp> createState() => _QuestClassAppState();
}

class _QuestClassAppState extends State<QuestClassApp> {
  final controller = AppController();

  @override
  void initState() {
    super.initState();
    controller.addListener(() => setState(() {}));
    controller.load();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: appDisplayName,
      builder: (context, child) {
        final media = MediaQuery.of(context);
        return MediaQuery(
          data: media.copyWith(textScaler: const TextScaler.linear(1.0)),
          child: DefaultTextHeightBehavior(
            textHeightBehavior: const TextHeightBehavior(applyHeightToFirstAscent: false, applyHeightToLastDescent: false),
            child: child ?? const SizedBox.shrink(),
          ),
        );
      },
      theme: buildTheme(controller.settings),
      home: controller.ready
          ? MainShell(controller: controller)
          : const Scaffold(body: Center(child: CircularProgressIndicator())),
    );
  }
}
'''


# Write patched files.
write(SRC / "models.dart", models)
write(SRC / "i18n.dart", i18n)
write(SRC / "app_controller.dart", app_controller)
write(SRC / "pixel_widgets.dart", pixel_widgets)
write(SRC / "stats_card.dart", stats_card)
write(SRC / "calendar_card.dart", calendar_card)
write(SRC / "home_page.dart", home_page)
write(SRC / "quest_card.dart", quest_card)
write(SRC / "history_page.dart", history_page)
write(SRC / "achievements_page.dart", achievements_page)
write(SRC / "main_shell.dart", main_shell)
write(SRC / "app.dart", app_dart)

print(f"""
DONE v5.

Display name is now: {APP_NAME}

Now run:
  flutter clean
  flutter pub get
  flutter run

Main changes:
- Renamed the app display to {APP_NAME}.
- Removed the ON DUE card from home.
- Calendar is full width, shows month names like "May 2026", and keeps previous/next month navigation.
- Fixed compact calendar overflow by shrinking calendar cells and avoiding overflowing text.
- Stats card now uses dynamic labels: AWESOME, VERY GOOD, GOOD, NOT BAD, LET'S TRY AGAIN, KEEP GOING, START NOW.
- Fixed STREAK/LEVEL text wrapping in the stats card.
- Removed the small 5-cube decorations.
- History now shows gained EXP and whether completion was on time or late.
- Added an Achievements tab with progress like 100% (1/1).
- Completion EXP is saved into quest history so it does not change later.

Backups were saved as *.bak_v5 beside each patched file.
""")
