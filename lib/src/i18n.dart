
import 'models.dart';

class L10n {
  L10n(this.language);
  final AppLanguage language;
  bool get id => language == AppLanguage.id;

  String get appName => appDisplayName;
  String get stats => id ? 'STATISTIK' : 'STATS';
  String get calendar => id ? 'KALENDER' : 'CALENDAR';
  String get homework => id ? 'TUGAS' : 'TASKS';
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
  String get createQuest => id ? 'BUAT' : 'CREATE';
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
  String get noQuest => id ? 'Belum ada tugas.' : 'No tasks yet.';
  String get sort => id ? 'Urutkan' : 'Sort';
  String get sortPriority => id ? 'Prioritas tertinggi' : 'Highest priority';
  String get sortExp => id ? 'EXP tertinggi' : 'Highest EXP';
  String get openLms => id ? 'Buka LMS' : 'Open LMS';
  String get favorite => id ? 'Favorit' : 'Favorite';
  String get resetData => id ? 'Reset semua data' : 'Reset all data';
  String get uiDesign => id ? 'Desain UI' : 'UI Design';
  String get compact => id ? 'Compact' : 'Compact';
  String get simple => id ? 'Simple' : 'Simple';
  String get languages => id ? 'Bahasa' : 'Language';
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
