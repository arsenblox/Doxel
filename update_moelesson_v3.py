from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
LIB = ROOT / "lib"
SRC = LIB / "src"
ASSETS_FONTS = ROOT / "assets" / "fonts"

if not (ROOT / "pubspec.yaml").exists():
    raise SystemExit("Run this script from your Flutter project root, the folder that contains pubspec.yaml")

SRC.mkdir(parents=True, exist_ok=True)
ASSETS_FONTS.mkdir(parents=True, exist_ok=True)

# Try to install Visitor TT2 font if you put visitor2.ttf / visitor2 (1).ttf in this project folder.
visitor_font_target = ASSETS_FONTS / "visitor2.ttf"
if not visitor_font_target.exists():
    for pattern in ["visitor*.ttf", "Visitor*.ttf", "VISITOR*.ttf"]:
        found = [p for p in ROOT.glob(pattern) if p.is_file()]
        if found:
            shutil.copyfile(found[0], visitor_font_target)
            print(f"Copied font: {found[0].name} -> assets/fonts/visitor2.ttf")
            break


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def patch_pubspec() -> None:
    pub = ROOT / "pubspec.yaml"
    text = pub.read_text(encoding="utf-8")

    # Keep the user's existing project name, but force compatible dependency versions.
    def ensure_dep(src: str, name: str, value: str) -> str:
        pattern = rf"^\s{{2}}{re.escape(name)}:\s*.*$"
        if re.search(pattern, src, flags=re.M):
            return re.sub(pattern, f"  {name}: {value}", src, flags=re.M)
        m = re.search(r"^dependencies:\s*$", src, flags=re.M)
        if not m:
            src += "\n\ndependencies:\n  flutter:\n    sdk: flutter\n"
            m = re.search(r"^dependencies:\s*$", src, flags=re.M)
        insert_at = m.end()
        return src[:insert_at] + f"\n  {name}: {value}" + src[insert_at:]

    for name, value in {
        "shared_preferences": "2.5.3",
        "image_picker": "1.1.2",
        "url_launcher": "6.3.1",
    }.items():
        text = ensure_dep(text, name, value)

    # Add Visitor font only when the user has the local ttf file.
    if visitor_font_target.exists():
        # Remove old generated QuestClass font block if present, then add a clean one.
        text = re.sub(
            r"\n\s*# QuestClass generated fonts start\n.*?\n\s*# QuestClass generated fonts end\n",
            "\n",
            text,
            flags=re.S,
        )
        flutter_match = re.search(r"^flutter:\s*$", text, flags=re.M)
        if flutter_match:
            font_block = """

  # QuestClass generated fonts start
  fonts:
    - family: Visitor
      fonts:
        - asset: assets/fonts/visitor2.ttf
  # QuestClass generated fonts end
"""
            # If pubspec already has a fonts section, do not risk corrupting it. User can merge manually.
            if "family: Visitor" not in text:
                if re.search(r"^\s{2}fonts:\s*$", text, flags=re.M):
                    print("pubspec already has fonts:. Visitor font file copied, but font block was not auto-added to avoid breaking existing fonts.")
                else:
                    text = text.rstrip() + font_block

    pub.write_text(text, encoding="utf-8")
    print("patched pubspec.yaml")


patch_pubspec()

write(LIB / "main.dart", r'''
import 'package:flutter/material.dart';

import 'src/app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const QuestClassApp());
}
''')

write(SRC / "models.dart", r'''
import 'dart:convert';

const String appDisplayName = 'QUESTCLASS';

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
  LmsLinkMode lmsLinkMode;
  String lmsFullUrl;
  LmsActivityType lmsActivityType;
  String lmsId;

  bool get isCompleted => completedAt != null;
  bool get isOverdue => !isCompleted && DateTime.now().isAfter(deadline);

  String get lmsUrl {
    if (lmsLinkMode == LmsLinkMode.fullUrl) return lmsFullUrl.trim();
    final cleanId = lmsId.trim();
    if (cleanId.isEmpty) return '';
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
''')

write(SRC / "i18n.dart", r'''
import 'models.dart';

class L10n {
  L10n(this.language);
  final AppLanguage language;
  bool get id => language == AppLanguage.id;

  String get appName => 'QUESTCLASS';
  String get stats => id ? 'STATISTIK' : 'STATS';
  String get onDue => id ? 'JATUH TEMPO' : 'ON DUE';
  String get calendar => id ? 'KALENDER' : 'CALENDAR';
  String get homework => id ? 'TUGAS' : 'HOMEWORK';
  String get history => id ? 'RIWAYAT' : 'HISTORY';
  String get gallery => id ? 'GALERI' : 'GALLERY';
  String get settings => id ? 'PENGATURAN' : 'SETTINGS';
  String get veryGood => id ? 'SANGAT BAIK!' : 'VERY GOOD!';
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
''')

write(SRC / "helpers.dart", r'''
import 'package:flutter/material.dart';

String two(int n) => n.toString().padLeft(2, '0');

String formatDate(DateTime d) => '${two(d.day)}/${two(d.month)}/${d.year}';
String formatTime(DateTime d) => '${two(d.hour)}:${two(d.minute)}';
String formatDateTime(DateTime d) => '${formatDate(d)} ${formatTime(d)}';

String remainingText(DateTime deadline) {
  final now = DateTime.now();
  if (now.isAfter(deadline)) return 'PASSED';
  final diff = deadline.difference(now);
  if (diff.inDays >= 1) return '${diff.inDays}D ${diff.inHours % 24}H';
  if (diff.inHours >= 1) return '${diff.inHours}H ${diff.inMinutes % 60}M';
  return '${diff.inMinutes.clamp(0, 999)}M';
}

Color priorityColor(String priorityName, BuildContext context) {
  switch (priorityName.toLowerCase()) {
    case 'urgent':
    case 'darurat':
      return const Color(0xFFFF4C67);
    case 'normal':
      return const Color(0xFFFFC928);
    default:
      return const Color(0xFF00FF44);
  }
}
''')

write(SRC / "app_theme.dart", r'''
import 'package:flutter/material.dart';

import 'models.dart';

class AppColors extends ThemeExtension<AppColors> {
  const AppColors({
    required this.bgTop,
    required this.bgBottom,
    required this.panel,
    required this.panelSoft,
    required this.text,
    required this.muted,
    required this.line,
    required this.accent,
  });

  final Color bgTop;
  final Color bgBottom;
  final Color panel;
  final Color panelSoft;
  final Color text;
  final Color muted;
  final Color line;
  final Color accent;

  static const dark = AppColors(
    bgTop: Color(0xFF0D0D17),
    bgBottom: Color(0xFF252A46),
    panel: Color(0xFF171927),
    panelSoft: Color(0xFF202338),
    text: Color(0xFFF5F5FF),
    muted: Color(0xFFA7A8B8),
    line: Color(0xFFE7E7F3),
    accent: Color(0xFF00A3FF),
  );

  static const light = AppColors(
    bgTop: Color(0xFFEDEFFF),
    bgBottom: Color(0xFFFFFFFF),
    panel: Color(0xFFF9FAFF),
    panelSoft: Color(0xFFE8EBFF),
    text: Color(0xFF161827),
    muted: Color(0xFF5E6475),
    line: Color(0xFF282C40),
    accent: Color(0xFF246BFE),
  );

  @override
  AppColors copyWith({Color? bgTop, Color? bgBottom, Color? panel, Color? panelSoft, Color? text, Color? muted, Color? line, Color? accent}) {
    return AppColors(
      bgTop: bgTop ?? this.bgTop,
      bgBottom: bgBottom ?? this.bgBottom,
      panel: panel ?? this.panel,
      panelSoft: panelSoft ?? this.panelSoft,
      text: text ?? this.text,
      muted: muted ?? this.muted,
      line: line ?? this.line,
      accent: accent ?? this.accent,
    );
  }

  @override
  ThemeExtension<AppColors> lerp(covariant ThemeExtension<AppColors>? other, double t) => this;
}

ThemeData buildTheme(AppSettings settings) {
  final colors = settings.themeMode == AppThemeMode.dark ? AppColors.dark : AppColors.light;
  final family = settings.fontStyle == PixelFontStyle.visitor ? 'Visitor' : 'monospace';
  final base = ThemeData(
    useMaterial3: true,
    brightness: settings.themeMode == AppThemeMode.dark ? Brightness.dark : Brightness.light,
    fontFamily: family,
    colorScheme: ColorScheme.fromSeed(
      seedColor: colors.accent,
      brightness: settings.themeMode == AppThemeMode.dark ? Brightness.dark : Brightness.light,
    ),
  );
  return base.copyWith(
    scaffoldBackgroundColor: colors.bgBottom,
    textTheme: base.textTheme.apply(fontFamily: family, bodyColor: colors.text, displayColor: colors.text),
    extensions: <ThemeExtension<dynamic>>[colors],
  );
}

AppColors appColors(BuildContext context) => Theme.of(context).extension<AppColors>()!;
''')

write(SRC / "app_controller.dart", r'''
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

  Quest? get topDueQuest {
    final items = activeQuests();
    if (items.isEmpty) return null;
    items.sort((a, b) {
      if (a.favorite != b.favorite) return a.favorite ? -1 : 1;
      return a.deadline.compareTo(b.deadline);
    });
    return items.first;
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
    q.completedAt = now;
    q.completionNotes = notes;
    q.photoPaths = photoPaths.take(10).toList();

    final gained = q.expGainAt(now);
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
''')

write(SRC / "pixel_widgets.dart", r'''
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
      child: Stack(
        children: <Widget>[
          Positioned(right: 20, top: 14, child: PixelCorners(color: c.muted.withValues(alpha: 0.22))),
          Padding(
            padding: padding,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                if (title != null) ...<Widget>[
                  Center(
                    child: Text(
                      title!,
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 2, color: c.text),
                    ),
                  ),
                  Center(child: Container(width: 250, height: 2, color: c.line.withValues(alpha: 0.82))),
                  const SizedBox(height: 14),
                ],
                Expanded(child: child),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class PixelCorners extends StatelessWidget {
  const PixelCorners({super.key, required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 42,
      height: 28,
      child: Stack(
        children: List<Widget>.generate(5, (i) {
          final x = (i % 3) * 10.0;
          final y = (i ~/ 3) * 10.0;
          return Positioned(left: x, top: y, child: Container(width: 8, height: 8, color: color));
        }),
      ),
    );
  }
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
          Text(text, style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 3)),
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
        child: Text('$percent%', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Colors.white)),
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
      label: Text(label, style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
      style: OutlinedButton.styleFrom(
        foregroundColor: filled ? c.panel : c.text,
        backgroundColor: filled ? c.line : Colors.transparent,
        side: BorderSide(color: c.line, width: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      ),
    );
  }
}
''')

write(SRC / "stats_card.dart", r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class StatsCard extends StatelessWidget {
  const StatsCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final s = controller.state;
    final active = controller.state.quests.where((q) => !q.isCompleted).length;
    final height = MediaQuery.sizeOf(context).width < 600 ? 270.0 : 300.0;
    return PixelPanel(
      title: l.stats,
      height: height,
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 20),
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Row(
            children: <Widget>[
              SizedBox(
                width: constraints.maxWidth * 0.31,
                child: Center(
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: DonutChart(
                      completed: s.completedOnTime,
                      late: s.lateCompleted,
                      onDue: active,
                      percent: s.completionPercent,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 22),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    FittedBox(
                      alignment: Alignment.centerLeft,
                      fit: BoxFit.scaleDown,
                      child: Text(l.veryGood, style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w900, letterSpacing: 3)),
                    ),
                    const SizedBox(height: 18),
                    _bar(context),
                    const SizedBox(height: 14),
                    Row(
                      children: <Widget>[
                        Expanded(child: _legend(context, l, active)),
                        Expanded(child: _miniStat(context, l.streak, '${s.streak}')),
                        Expanded(child: _miniStat(context, l.level, '${s.level}\n${s.exp}/${s.expNeeded}')),
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
          padding: const EdgeInsets.only(bottom: 5),
          child: Row(children: <Widget>[
            Container(width: 14, height: 14, color: color),
            const SizedBox(width: 7),
            Expanded(child: Text(text, overflow: TextOverflow.ellipsis, style: TextStyle(color: c.text, fontSize: 13, fontWeight: FontWeight.w900))),
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
      padding: const EdgeInsets.only(left: 8),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: c.text, letterSpacing: 2)),
          Container(height: 2, color: c.line.withValues(alpha: 0.85)),
          const SizedBox(height: 4),
          Text(value, textAlign: TextAlign.center, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: c.text, height: 1.15)),
        ],
      ),
    );
  }
}
''')

write(SRC / "calendar_card.dart", r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'helpers.dart';
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
    final cells = <Widget>[];
    for (int i = 1; i < firstWeekday; i++) {
      cells.add(const SizedBox.shrink());
    }
    for (int d = 1; d <= days; d++) {
      final date = DateTime(month.year, month.month, d);
      final count = widget.controller.activeQuests().where((q) => DateUtils.isSameDay(q.deadline, date)).length;
      final isToday = DateUtils.isSameDay(date, DateTime.now());
      final isSelected = selected != null && DateUtils.isSameDay(date, selected);
      cells.add(InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => selected = date),
        child: Container(
          decoration: BoxDecoration(
            color: isSelected ? c.line.withValues(alpha: 0.18) : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: isToday ? Border.all(color: c.accent, width: 2) : null,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Text('$d', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: c.text)),
              const SizedBox(height: 2),
              if (count > 0) Container(width: 6, height: 6, decoration: const BoxDecoration(color: Color(0xFFFFC400), shape: BoxShape.circle)),
            ],
          ),
        ),
      ));
    }

    final selectedTasks = selected == null
        ? <dynamic>[]
        : widget.controller.activeQuests().where((q) => DateUtils.isSameDay(q.deadline, selected)).toList();

    return PixelPanel(
      title: l.calendar,
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
      child: Column(
        children: <Widget>[
          Row(
            children: <Widget>[
              IconButton(onPressed: () => setState(() => month = DateTime(month.year, month.month - 1)), icon: const Icon(Icons.chevron_left)),
              Expanded(
                child: Center(
                  child: Text('${month.year}/${two(month.month)}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 2)),
                ),
              ),
              IconButton(onPressed: () => setState(() => month = DateTime(month.year, month.month + 1)), icon: const Icon(Icons.chevron_right)),
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: const <Widget>[
              _Week('M'), _Week('T'), _Week('W'), _Week('T'), _Week('F'), _Week('S'), _Week('S'),
            ],
          ),
          const SizedBox(height: 6),
          Expanded(
            child: GridView.count(
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 7,
              childAspectRatio: 1.05,
              mainAxisSpacing: 2,
              crossAxisSpacing: 2,
              children: cells,
            ),
          ),
          if (selectedTasks.isNotEmpty)
            SizedBox(
              height: 35,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: selectedTasks.map<Widget>((q) => Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Chip(label: Text(q.title, overflow: TextOverflow.ellipsis)),
                )).toList(),
              ),
            ),
        ],
      ),
    );
  }
}

class _Week extends StatelessWidget {
  const _Week(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Text(text, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11));
}
''')

write(SRC / "quest_card.dart", r'''
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

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
        borderRadius: BorderRadius.circular(compact ? 8 : 28),
        border: Border.all(color: c.line.withValues(alpha: 0.8), width: 2),
      ),
      child: Stack(
        children: <Widget>[
          Positioned(right: 8, top: 4, child: PixelCorners(color: c.muted.withValues(alpha: 0.22))),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(quest.title.toUpperCase(), overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: compact ? 14 : 24, fontWeight: FontWeight.w900, letterSpacing: 2)),
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
                      Expanded(child: PixelButton(label: l.openLms, icon: Icons.open_in_new, onPressed: () => launchUrl(Uri.parse(quest.lmsUrl), mode: LaunchMode.externalApplication))),
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
        ],
      ),
    );
  }
}

class OnDueCard extends StatelessWidget {
  const OnDueCard({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final q = controller.topDueQuest;
    return PixelPanel(
      title: l.onDue,
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      child: q == null
          ? Center(child: Text(l.noQuest, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w900)))
          : QuestCard(controller: controller, quest: q, compact: true),
    );
  }
}
''')

write(SRC / "create_quest_sheet.dart", r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'helpers.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

Future<void> showCreateQuestSheet(BuildContext context, AppController controller) async {
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => CreateQuestSheet(controller: controller),
  );
}

class CreateQuestSheet extends StatefulWidget {
  const CreateQuestSheet({super.key, required this.controller});
  final AppController controller;

  @override
  State<CreateQuestSheet> createState() => _CreateQuestSheetState();
}

class _CreateQuestSheetState extends State<CreateQuestSheet> {
  final title = TextEditingController();
  final desc = TextEditingController();
  final fullUrl = TextEditingController();
  final lmsId = TextEditingController();
  Priority priority = Priority.normal;
  WorkType workType = WorkType.school;
  LmsLinkMode linkMode = LmsLinkMode.fullUrl;
  LmsActivityType activityType = LmsActivityType.assign;
  DateTime deadline = DateTime.now().add(const Duration(days: 7));

  @override
  void dispose() {
    title.dispose();
    desc.dispose();
    fullUrl.dispose();
    lmsId.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    return DraggableScrollableSheet(
      initialChildSize: 0.86,
      maxChildSize: 0.96,
      minChildSize: 0.45,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(color: c.panel, borderRadius: const BorderRadius.vertical(top: Radius.circular(32))),
          padding: EdgeInsets.only(left: 20, right: 20, top: 18, bottom: MediaQuery.viewInsetsOf(context).bottom + 20),
          child: ListView(
            controller: scrollController,
            children: <Widget>[
              Center(child: Container(width: 90, height: 5, decoration: BoxDecoration(color: c.line, borderRadius: BorderRadius.circular(99)))),
              const SizedBox(height: 18),
              Text(l.createQuest, textAlign: TextAlign.center, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 2)),
              const SizedBox(height: 18),
              TextField(controller: title, decoration: InputDecoration(labelText: l.title, border: const OutlineInputBorder())),
              const SizedBox(height: 12),
              TextField(controller: desc, minLines: 2, maxLines: 4, decoration: InputDecoration(labelText: l.description, border: const OutlineInputBorder())),
              const SizedBox(height: 12),
              DropdownButtonFormField<Priority>(
                value: priority,
                decoration: InputDecoration(labelText: l.priority, border: const OutlineInputBorder()),
                items: Priority.values.map((p) => DropdownMenuItem(value: p, child: Text('${l.priorityName(p)}  +${p.baseExp} EXP'))).toList(),
                onChanged: (v) => setState(() => priority = v ?? priority),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<WorkType>(
                value: workType,
                decoration: InputDecoration(labelText: l.typeOfWork, border: const OutlineInputBorder()),
                items: WorkType.values.map((t) => DropdownMenuItem(value: t, child: Text(l.workTypeName(t)))).toList(),
                onChanged: (v) => setState(() => workType = v ?? workType),
              ),
              const SizedBox(height: 12),
              ListTile(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: BorderSide(color: c.line.withValues(alpha: 0.4))),
                title: Text('${l.deadline}: ${formatDateTime(deadline)}'),
                subtitle: Text('Max ${priority.maxDeadlineDays} days for ${l.priorityName(priority)}'),
                trailing: const Icon(Icons.calendar_month),
                onTap: pickDeadline,
              ),
              const SizedBox(height: 12),
              SegmentedButton<LmsLinkMode>(
                segments: <ButtonSegment<LmsLinkMode>>[
                  ButtonSegment(value: LmsLinkMode.fullUrl, label: Text(l.fullUrl)),
                  ButtonSegment(value: LmsLinkMode.moodleId, label: Text(l.lmsId)),
                ],
                selected: <LmsLinkMode>{linkMode},
                onSelectionChanged: (v) => setState(() => linkMode = v.first),
              ),
              const SizedBox(height: 12),
              if (linkMode == LmsLinkMode.fullUrl)
                TextField(controller: fullUrl, decoration: InputDecoration(labelText: l.fullUrl, border: const OutlineInputBorder()))
              else ...<Widget>[
                DropdownButtonFormField<LmsActivityType>(
                  value: activityType,
                  decoration: const InputDecoration(labelText: 'Type', border: OutlineInputBorder()),
                  items: const <DropdownMenuItem<LmsActivityType>>[
                    DropdownMenuItem(value: LmsActivityType.assign, child: Text('ASSIGN')),
                    DropdownMenuItem(value: LmsActivityType.quiz, child: Text('QUIZ')),
                  ],
                  onChanged: (v) => setState(() => activityType = v ?? activityType),
                ),
                const SizedBox(height: 12),
                TextField(controller: lmsId, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: l.lmsId, border: const OutlineInputBorder())),
              ],
              const SizedBox(height: 18),
              PixelButton(label: l.save, filled: true, onPressed: saveQuest),
            ],
          ),
        );
      },
    );
  }

  Future<void> pickDeadline() async {
    final date = await showDatePicker(
      context: context,
      initialDate: deadline,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(Duration(days: priority.maxDeadlineDays)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(deadline));
    if (time == null) return;
    setState(() => deadline = DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }

  Future<void> saveQuest() async {
    if (title.text.trim().isEmpty) return;
    final quest = Quest(
      id: newId(),
      title: title.text.trim(),
      description: desc.text.trim(),
      priority: priority,
      workType: workType,
      createdAt: DateTime.now(),
      deadline: deadline,
      lmsLinkMode: linkMode,
      lmsFullUrl: fullUrl.text.trim(),
      lmsActivityType: activityType,
      lmsId: lmsId.text.trim(),
    );
    final err = await widget.controller.addQuest(quest);
    if (!mounted) return;
    if (err != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
      return;
    }
    Navigator.pop(context);
  }
}
''')

write(SRC / "complete_quest_sheet.dart", r'''
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

Future<void> showCompleteQuestSheet(BuildContext context, AppController controller, Quest quest) async {
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => CompleteQuestSheet(controller: controller, quest: quest),
  );
}

class CompleteQuestSheet extends StatefulWidget {
  const CompleteQuestSheet({super.key, required this.controller, required this.quest});
  final AppController controller;
  final Quest quest;

  @override
  State<CompleteQuestSheet> createState() => _CompleteQuestSheetState();
}

class _CompleteQuestSheetState extends State<CompleteQuestSheet> {
  final notes = TextEditingController();
  final picker = ImagePicker();
  final photos = <String>[];

  @override
  void dispose() {
    notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = L10n(widget.controller.settings.language);
    final c = appColors(context);
    return Container(
      decoration: BoxDecoration(color: c.panel, borderRadius: const BorderRadius.vertical(top: Radius.circular(32))),
      padding: EdgeInsets.only(left: 20, right: 20, top: 20, bottom: MediaQuery.viewInsetsOf(context).bottom + 20),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Center(child: Container(width: 90, height: 5, decoration: BoxDecoration(color: c.line, borderRadius: BorderRadius.circular(99)))),
              const SizedBox(height: 18),
              Text(widget.quest.title.toUpperCase(), textAlign: TextAlign.center, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, letterSpacing: 2)),
              const SizedBox(height: 14),
              TextField(controller: notes, minLines: 3, maxLines: 6, decoration: InputDecoration(labelText: l.notesOptional, border: const OutlineInputBorder())),
              const SizedBox(height: 12),
              Text(l.photosOptional, style: const TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: <Widget>[
                  for (final p in photos)
                    Stack(
                      children: <Widget>[
                        ClipRRect(borderRadius: BorderRadius.circular(14), child: Image.file(File(p), width: 74, height: 74, fit: BoxFit.cover)),
                        Positioned(
                          right: 0,
                          top: 0,
                          child: InkWell(
                            onTap: () => setState(() => photos.remove(p)),
                            child: Container(color: Colors.black54, child: const Icon(Icons.close, size: 18)),
                          ),
                        ),
                      ],
                    ),
                  if (photos.length < 10)
                    InkWell(
                      onTap: pickImages,
                      child: Container(width: 74, height: 74, decoration: BoxDecoration(border: Border.all(color: c.line, width: 2), borderRadius: BorderRadius.circular(14)), child: const Icon(Icons.add_photo_alternate)),
                    ),
                ],
              ),
              const SizedBox(height: 18),
              PixelButton(label: l.complete, filled: true, onPressed: finish),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> pickImages() async {
    final picked = await picker.pickMultiImage(imageQuality: 82);
    if (!mounted || picked.isEmpty) return;
    setState(() {
      for (final x in picked) {
        if (photos.length >= 10) break;
        photos.add(x.path);
      }
    });
  }

  Future<void> finish() async {
    await widget.controller.completeQuest(widget.quest.id, notes: notes.text.trim(), photoPaths: photos);
    if (!mounted) return;
    Navigator.pop(context);
  }
}
''')

write(SRC / "home_page.dart", r'''
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
        width: 70,
        height: 70,
        child: FloatingActionButton(
          heroTag: 'createQuest',
          onPressed: () => showCreateQuestSheet(context, controller),
          child: const Icon(Icons.add, size: 38),
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
                if (compact)
                  SizedBox(
                    height: 360,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Expanded(child: OnDueCard(controller: controller)),
                        const SizedBox(width: 22),
                        Expanded(child: CalendarCard(controller: controller)),
                      ],
                    ),
                  )
                else ...<Widget>[
                  SizedBox(height: 260, child: OnDueCard(controller: controller)),
                  const SizedBox(height: 18),
                  SizedBox(height: 410, child: CalendarCard(controller: controller)),
                ],
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
''')

write(SRC / "history_page.dart", r'''
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
                    Text(q.title.toUpperCase(), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2)),
                    const SizedBox(height: 4),
                    Text('${l.completed}: ${formatDateTime(q.completedAt ?? q.deadline)}'),
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
''')

write(SRC / "gallery_page.dart", r'''
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'pixel_widgets.dart';

class GalleryPage extends StatelessWidget {
  const GalleryPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final c = appColors(context);
    final quests = controller.completedQuests().where((q) => q.photoPaths.isNotEmpty).toList();
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 120),
        children: <Widget>[
          SectionTitle(l.gallery),
          Text(
            'Images are grouped by quest/course so it is easier to pick the correct file when uploading to LMS.',
            style: TextStyle(color: c.muted, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 16),
          if (quests.isEmpty)
            Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(l.noQuest)))
          else
            for (final q in quests)
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: c.panel.withValues(alpha: 0.85), borderRadius: BorderRadius.circular(24), border: Border.all(color: c.line.withValues(alpha: 0.55), width: 2)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Expanded(child: Text(q.title.toUpperCase(), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2))),
                        if (q.lmsUrl.isNotEmpty)
                          IconButton(onPressed: () => launchUrl(Uri.parse(q.lmsUrl), mode: LaunchMode.externalApplication), icon: const Icon(Icons.open_in_new)),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: <Widget>[
                        for (final p in q.photoPaths)
                          ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.file(File(p), width: 92, height: 92, fit: BoxFit.cover)),
                      ],
                    ),
                  ],
                ),
              ),
        ],
      ),
    );
  }
}
''')

write(SRC / "settings_page.dart", r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'i18n.dart';
import 'models.dart';
import 'pixel_widgets.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final l = L10n(controller.settings.language);
    final s = controller.settings;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(l.settings), backgroundColor: Colors.transparent),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 40),
        children: <Widget>[
          SectionTitle(l.settings),
          _tile(
            context,
            title: l.language,
            child: SegmentedButton<AppLanguage>(
              segments: const <ButtonSegment<AppLanguage>>[
                ButtonSegment(value: AppLanguage.en, label: Text('EN')),
                ButtonSegment(value: AppLanguage.id, label: Text('ID')),
              ],
              selected: <AppLanguage>{s.language},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(language: v.first, themeMode: s.themeMode, uiStyle: s.uiStyle, fontStyle: s.fontStyle, reminderMinutes: s.reminderMinutes)),
            ),
          ),
          _tile(
            context,
            title: l.theme,
            child: SegmentedButton<AppThemeMode>(
              segments: const <ButtonSegment<AppThemeMode>>[
                ButtonSegment(value: AppThemeMode.dark, label: Text('BLACK')),
                ButtonSegment(value: AppThemeMode.light, label: Text('WHITE')),
              ],
              selected: <AppThemeMode>{s.themeMode},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(language: s.language, themeMode: v.first, uiStyle: s.uiStyle, fontStyle: s.fontStyle, reminderMinutes: s.reminderMinutes)),
            ),
          ),
          _tile(
            context,
            title: l.uiDesign,
            child: SegmentedButton<UiStyle>(
              segments: <ButtonSegment<UiStyle>>[
                ButtonSegment(value: UiStyle.simple, label: Text(l.simple)),
                ButtonSegment(value: UiStyle.compact, label: Text(l.compact)),
              ],
              selected: <UiStyle>{s.uiStyle},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(language: s.language, themeMode: s.themeMode, uiStyle: v.first, fontStyle: s.fontStyle, reminderMinutes: s.reminderMinutes)),
            ),
          ),
          _tile(
            context,
            title: l.font,
            child: SegmentedButton<PixelFontStyle>(
              segments: const <ButtonSegment<PixelFontStyle>>[
                ButtonSegment(value: PixelFontStyle.visitor, label: Text('Visitor TT2')),
                ButtonSegment(value: PixelFontStyle.classic, label: Text('Classic')),
              ],
              selected: <PixelFontStyle>{s.fontStyle},
              onSelectionChanged: (v) => controller.updateSettings(AppSettings(language: s.language, themeMode: s.themeMode, uiStyle: s.uiStyle, fontStyle: v.first, reminderMinutes: s.reminderMinutes)),
            ),
          ),
          _tile(
            context,
            title: l.reminders,
            child: Column(
              children: AppSettings.defaultReminderMinutes.map((m) {
                final enabled = s.reminderMinutes.contains(m);
                return CheckboxListTile(
                  value: enabled,
                  title: Text(l.reminderLabel(m)),
                  onChanged: (v) {
                    final next = List<int>.from(s.reminderMinutes);
                    if (v == true && !next.contains(m)) next.add(m);
                    if (v == false) next.remove(m);
                    next.sort((a, b) => b.compareTo(a));
                    controller.updateSettings(AppSettings(language: s.language, themeMode: s.themeMode, uiStyle: s.uiStyle, fontStyle: s.fontStyle, reminderMinutes: next));
                  },
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () async {
              final ok = await showDialog<bool>(
                context: context,
                builder: (_) => AlertDialog(
                  title: Text(l.resetData),
                  content: const Text('This will delete all quests, history, exp, level, and streak.'),
                  actions: <Widget>[
                    TextButton(onPressed: () => Navigator.pop(context, false), child: Text(l.cancel)),
                    FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(l.resetData)),
                  ],
                ),
              );
              if (ok == true) controller.resetAllData();
            },
            icon: const Icon(Icons.delete_forever),
            label: Text(l.resetData),
          ),
        ],
      ),
    );
  }

  Widget _tile(BuildContext context, {required String title, required Widget child}) {
    final c = appColors(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: c.panel.withValues(alpha: 0.86), borderRadius: BorderRadius.circular(24), border: Border.all(color: c.line.withValues(alpha: 0.45), width: 2)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: <Widget>[
        Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 2)),
        const SizedBox(height: 12),
        child,
      ]),
    );
  }
}
''')

write(SRC / "main_shell.dart", r'''
import 'package:flutter/material.dart';

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
                padding: const EdgeInsets.fromLTRB(28, 26, 28, 18),
                child: Row(
                  children: <Widget>[
                    Expanded(child: Text(l.appName, style: const TextStyle(fontSize: 46, fontWeight: FontWeight.w900, letterSpacing: 4))),
                    IconButton(iconSize: 34, onPressed: () {}, icon: const Icon(Icons.notifications)),
                    const SizedBox(width: 10),
                    IconButton(iconSize: 36, onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SettingsPage(controller: widget.controller))), icon: const Icon(Icons.settings)),
                  ],
                ),
              ),
              Padding(padding: const EdgeInsets.symmetric(horizontal: 28), child: Container(height: 4, color: c.line.withValues(alpha: 0.9))),
              const SizedBox(height: 16),
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

  @override
  void initState() {
    super.initState();
    controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 650))..forward();
    scale = CurvedAnimation(parent: controller, curve: Curves.elasticOut);
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
        child: Container(
          padding: const EdgeInsets.all(26),
          decoration: BoxDecoration(
            color: c.panel,
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: c.line, width: 3),
            boxShadow: <BoxShadow>[BoxShadow(color: c.accent.withValues(alpha: 0.28), blurRadius: 30, spreadRadius: 8)],
          ),
          child: Column(mainAxisSize: MainAxisSize.min, children: <Widget>[
            const Icon(Icons.auto_awesome, size: 76, color: Color(0xFFFFC400)),
            const SizedBox(height: 10),
            const Text('LEVEL UP!', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w900, letterSpacing: 3)),
            const SizedBox(height: 8),
            Text('LEVEL ${widget.level}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
            const SizedBox(height: 18),
            FilledButton(onPressed: () => Navigator.pop(context), child: const Text('OK')),
          ]),
        ),
      ),
    );
  }
}
''')

write(SRC / "app.dart", r'''
import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'app_theme.dart';
import 'main_shell.dart';

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
      title: 'QuestClass',
      theme: buildTheme(controller.settings),
      home: controller.ready
          ? MainShell(controller: controller)
          : const Scaffold(body: Center(child: CircularProgressIndicator())),
    );
  }
}
''')

print("""

DONE.
Next run:
  flutter clean
  flutter pub get
  flutter run

Notes:
- This uses a new clean storage key, so old prototype data will not appear.
- Put visitor2.ttf or visitor2 (1).ttf beside this script before running if you want Visitor TT2 installed automatically.
- Native Android gallery/provider integration is not included; the app now has an LMS Gallery page grouped by quest/course to make manual LMS upload easier.
""")
