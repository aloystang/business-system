const path = require("path");
const fs = require("fs");
const Database = require("better-sqlite3");

const dataDir = process.env.DATA_DIR || __dirname;
fs.mkdirSync(dataDir, { recursive: true });
const dbFile = path.join(dataDir, "data.sqlite");
const db = new Database(dbFile);

db.pragma("foreign_keys = ON");

function nowIso() {
  return new Date().toISOString();
}

function parseDate(dateStr) {
  const parts = dateStr.split("-").map((v) => Number(v));
  if (parts.length !== 3 || parts.some((v) => Number.isNaN(v))) {
    return null;
  }
  return new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
}

function parseLocalDate(dateStr) {
  const parts = dateStr.split("-").map((v) => Number(v));
  if (parts.length !== 3 || parts.some((v) => Number.isNaN(v))) {
    return null;
  }
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function formatDate(date) {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  const d = String(date.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatLocalDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function getRecentDates(endDateStr, length) {
  const end = parseDate(endDateStr);
  if (!end) return [];
  const dates = [];
  for (let i = length - 1; i >= 0; i -= 1) {
    const d = new Date(end);
    d.setUTCDate(d.getUTCDate() - i);
    dates.push(formatDate(d));
  }
  return dates;
}

function getWeekRangeForDate(dateStr) {
  const date = parseLocalDate(dateStr);
  if (!date) return null;
  const day = date.getDay();
  const diff = (day + 6) % 7;
  const monday = new Date(date);
  monday.setDate(date.getDate() - diff);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return {
    weekStart: formatLocalDate(monday),
    weekEnd: formatLocalDate(sunday),
  };
}

function hasConsecutiveCheckins(memberId, endDateStr, length) {
  const dates = getRecentDates(endDateStr, length);
  if (dates.length === 0) return false;
  const rows = db
    .prepare(
      "SELECT date FROM checkins WHERE member_id = ? AND date BETWEEN ? AND ?"
    )
    .all(memberId, dates[0], dates[dates.length - 1]);
  const set = new Set(rows.map((row) => row.date));
  return dates.every((d) => set.has(d));
}

function init() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS teams (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS members (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      team_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS checkins (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      member_id INTEGER NOT NULL,
      team_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      note TEXT,
      created_at TEXT NOT NULL,
      UNIQUE(member_id, date),
      FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
      FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS checkin_photos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      checkin_id INTEGER NOT NULL,
      path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(checkin_id) REFERENCES checkins(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS challenges (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      team_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      target_total INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS badge_definitions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      description TEXT NOT NULL,
      rule_type TEXT NOT NULL,
      rule_value INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS member_badges (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      member_id INTEGER NOT NULL,
      badge_id INTEGER NOT NULL,
      awarded_at TEXT NOT NULL,
      UNIQUE(member_id, badge_id),
      FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
      FOREIGN KEY(badge_id) REFERENCES badge_definitions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS weekly_summaries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      member_id INTEGER NOT NULL,
      team_id INTEGER NOT NULL,
      week_start TEXT NOT NULL,
      week_end TEXT NOT NULL,
      checkin_count INTEGER NOT NULL,
      missing_count INTEGER NOT NULL,
      penalty_amount INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE(member_id, week_start),
      FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
      FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ledger_entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      team_id INTEGER NOT NULL,
      member_id INTEGER NOT NULL,
      week_start TEXT NOT NULL,
      amount INTEGER NOT NULL,
      type TEXT NOT NULL,
      note TEXT,
      created_at TEXT NOT NULL,
      UNIQUE(member_id, week_start, type),
      FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
      FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );
  `);

  const badgeRows = [
    {
      code: "CHECKIN_5",
      name: "Consistency Starter",
      description: "5 total check-ins",
      ruleType: "total_checkins",
      ruleValue: 5,
    },
    {
      code: "CHECKIN_10",
      name: "Momentum Builder",
      description: "10 total check-ins",
      ruleType: "total_checkins",
      ruleValue: 10,
    },
    {
      code: "STREAK_7",
      name: "7-Day Streak",
      description: "7 consecutive days",
      ruleType: "streak_days",
      ruleValue: 7,
    },
  ];

  const insertBadge = db.prepare(
    "INSERT OR IGNORE INTO badge_definitions (code, name, description, rule_type, rule_value) VALUES (?, ?, ?, ?, ?)"
  );

  for (const badge of badgeRows) {
    insertBadge.run(
      badge.code,
      badge.name,
      badge.description,
      badge.ruleType,
      badge.ruleValue
    );
  }
}

function listTeams() {
  return db
    .prepare("SELECT id, name, created_at FROM teams ORDER BY id DESC")
    .all();
}

function getTeam(teamId) {
  return db
    .prepare("SELECT id, name, created_at FROM teams WHERE id = ?")
    .get(teamId);
}

function createTeam(name) {
  const now = nowIso();
  const info = db
    .prepare("INSERT INTO teams (name, created_at) VALUES (?, ?)")
    .run(name, now);
  return getTeam(info.lastInsertRowid);
}

function listMembers(teamId) {
  return db
    .prepare(
      "SELECT id, team_id, name, created_at FROM members WHERE team_id = ? ORDER BY id DESC"
    )
    .all(teamId);
}

function getMember(memberId) {
  return db
    .prepare(
      "SELECT id, team_id, name, created_at FROM members WHERE id = ?"
    )
    .get(memberId);
}

function createMember(teamId, name) {
  const now = nowIso();
  const info = db
    .prepare(
      "INSERT INTO members (team_id, name, created_at) VALUES (?, ?, ?)"
    )
    .run(teamId, name, now);
  return getMember(info.lastInsertRowid);
}

function createCheckin(teamId, memberId, date, note) {
  const now = nowIso();
  const info = db
    .prepare(
      "INSERT OR IGNORE INTO checkins (member_id, team_id, date, note, created_at) VALUES (?, ?, ?, ?, ?)"
    )
    .run(memberId, teamId, date, note || null, now);

  if (info.changes === 0) {
    return { created: false };
  }

  const checkin = db
    .prepare(
      "SELECT id, member_id, team_id, date, note, created_at FROM checkins WHERE id = ?"
    )
    .get(info.lastInsertRowid);

  return { created: true, checkin };
}

function addCheckinPhotos(checkinId, paths) {
  if (!paths.length) return;
  const now = nowIso();
  const stmt = db.prepare(
    "INSERT INTO checkin_photos (checkin_id, path, created_at) VALUES (?, ?, ?)"
  );
  const insertMany = db.transaction((items) => {
    for (const item of items) {
      stmt.run(checkinId, item, now);
    }
  });
  insertMany(paths);
}

function listCheckins(teamId, date, limit = 50) {
  let rows;
  if (date) {
    rows = db
      .prepare(
        "SELECT c.id, c.member_id, c.team_id, c.date, c.note, c.created_at, m.name as member_name FROM checkins c JOIN members m ON m.id = c.member_id WHERE c.team_id = ? AND c.date = ? ORDER BY c.created_at DESC"
      )
      .all(teamId, date);
  } else {
    rows = db
      .prepare(
        "SELECT c.id, c.member_id, c.team_id, c.date, c.note, c.created_at, m.name as member_name FROM checkins c JOIN members m ON m.id = c.member_id WHERE c.team_id = ? ORDER BY c.created_at DESC LIMIT ?"
      )
      .all(teamId, limit);
  }

  const ids = rows.map((row) => row.id);
  const photoMap = new Map();
  if (ids.length) {
    const placeholders = ids.map(() => "?").join(",");
    const photos = db
      .prepare(
        `SELECT checkin_id, path FROM checkin_photos WHERE checkin_id IN (${placeholders}) ORDER BY id ASC`
      )
      .all(...ids);
    for (const photo of photos) {
      if (!photoMap.has(photo.checkin_id)) {
        photoMap.set(photo.checkin_id, []);
      }
      photoMap.get(photo.checkin_id).push(photo.path);
    }
  }

  return rows.map((row) => ({
    ...row,
    photos: photoMap.get(row.id) || [],
  }));
}

function getTeamStats(teamId, startDate, endDate) {
  const total = db
    .prepare(
      "SELECT COUNT(*) as count FROM checkins WHERE team_id = ? AND date BETWEEN ? AND ?"
    )
    .get(teamId, startDate, endDate).count;

  const activeMembers = db
    .prepare(
      "SELECT COUNT(DISTINCT member_id) as count FROM checkins WHERE team_id = ? AND date BETWEEN ? AND ?"
    )
    .get(teamId, startDate, endDate).count;

  return { totalCheckins: total, activeMembers };
}

function getLeaderboard(teamId, startDate, endDate, limit = 10) {
  return db
    .prepare(
      "SELECT m.id, m.name, COUNT(c.id) as checkins FROM members m LEFT JOIN checkins c ON c.member_id = m.id AND c.team_id = m.team_id AND c.date BETWEEN ? AND ? WHERE m.team_id = ? GROUP BY m.id ORDER BY checkins DESC, m.name ASC LIMIT ?"
    )
    .all(startDate, endDate, teamId, limit);
}

function createChallenge(teamId, name, startDate, endDate, targetTotal) {
  const now = nowIso();
  const info = db
    .prepare(
      "INSERT INTO challenges (team_id, name, start_date, end_date, target_total, created_at) VALUES (?, ?, ?, ?, ?, ?)"
    )
    .run(teamId, name, startDate, endDate, targetTotal, now);

  return db
    .prepare(
      "SELECT id, team_id, name, start_date, end_date, target_total, created_at FROM challenges WHERE id = ?"
    )
    .get(info.lastInsertRowid);
}

function listChallenges(teamId) {
  const rows = db
    .prepare(
      "SELECT id, team_id, name, start_date, end_date, target_total, created_at FROM challenges WHERE team_id = ? ORDER BY created_at DESC"
    )
    .all(teamId);

  return rows.map((row) => {
    const progress = db
      .prepare(
        "SELECT COUNT(*) as count FROM checkins WHERE team_id = ? AND date BETWEEN ? AND ?"
      )
      .get(teamId, row.start_date, row.end_date).count;

    return {
      ...row,
      progress,
      completed: progress >= row.target_total,
    };
  });
}

function listMemberBadges(memberId) {
  return db
    .prepare(
      "SELECT b.code, b.name, b.description, mb.awarded_at FROM member_badges mb JOIN badge_definitions b ON b.id = mb.badge_id WHERE mb.member_id = ? ORDER BY mb.awarded_at DESC"
    )
    .all(memberId);
}

function maybeAwardBadges(memberId, date) {
  const awarded = [];
  const total = db
    .prepare("SELECT COUNT(*) as count FROM checkins WHERE member_id = ?")
    .get(memberId).count;

  const awardBadge = (code) => {
    const badge = db
      .prepare(
        "SELECT id, code, name, description FROM badge_definitions WHERE code = ?"
      )
      .get(code);

    if (!badge) return;

    const info = db
      .prepare(
        "INSERT OR IGNORE INTO member_badges (member_id, badge_id, awarded_at) VALUES (?, ?, ?)"
      )
      .run(memberId, badge.id, nowIso());

    if (info.changes > 0) {
      awarded.push(badge);
    }
  };

  if (total >= 5) {
    awardBadge("CHECKIN_5");
  }

  if (total >= 10) {
    awardBadge("CHECKIN_10");
  }

  if (hasConsecutiveCheckins(memberId, date, 7)) {
    awardBadge("STREAK_7");
  }

  return awarded;
}

function settleWeek(teamId, weekStartStr) {
  const range = getWeekRangeForDate(weekStartStr);
  if (!range) return null;
  const { weekStart, weekEnd } = range;
  const members = listMembers(teamId);
  const summaryStmt = db.prepare(
    "INSERT INTO weekly_summaries (member_id, team_id, week_start, week_end, checkin_count, missing_count, penalty_amount, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(member_id, week_start) DO UPDATE SET checkin_count = excluded.checkin_count, missing_count = excluded.missing_count, penalty_amount = excluded.penalty_amount, week_end = excluded.week_end"
  );
  const insertLedger = db.prepare(
    "INSERT INTO ledger_entries (team_id, member_id, week_start, amount, type, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(member_id, week_start, type) DO UPDATE SET amount = excluded.amount, note = excluded.note"
  );
  const deleteLedger = db.prepare(
    "DELETE FROM ledger_entries WHERE member_id = ? AND week_start = ? AND type = ?"
  );

  const results = [];
  const now = nowIso();
  const settleTx = db.transaction(() => {
    for (const member of members) {
      const count = db
        .prepare(
          "SELECT COUNT(*) as count FROM checkins WHERE member_id = ? AND date BETWEEN ? AND ?"
        )
        .get(member.id, weekStart, weekEnd).count;
      const missing = Math.max(0, 3 - count);
      const penalty = missing * 100;
      summaryStmt.run(
        member.id,
        teamId,
        weekStart,
        weekEnd,
        count,
        missing,
        penalty,
        now
      );

      if (penalty > 0) {
        insertLedger.run(
          teamId,
          member.id,
          weekStart,
          -penalty,
          "penalty",
          `本周未达标，扣款 ${penalty} 元`,
          now
        );
      } else {
        deleteLedger.run(member.id, weekStart, "penalty");
      }

      results.push({
        memberId: member.id,
        memberName: member.name,
        checkins: count,
        missing,
        penalty,
      });
    }
  });

  settleTx();

  return { weekStart, weekEnd, results };
}

function listWeeklySummaries(teamId, limit = 50) {
  return db
    .prepare(
      "SELECT ws.week_start, ws.week_end, ws.checkin_count, ws.missing_count, ws.penalty_amount, m.name as member_name FROM weekly_summaries ws JOIN members m ON m.id = ws.member_id WHERE ws.team_id = ? ORDER BY ws.week_start DESC, m.name ASC LIMIT ?"
    )
    .all(teamId, limit);
}

function listLedger(teamId, limit = 50) {
  return db
    .prepare(
      "SELECT l.week_start, l.amount, l.type, l.note, l.created_at, m.name as member_name FROM ledger_entries l JOIN members m ON m.id = l.member_id WHERE l.team_id = ? ORDER BY l.created_at DESC LIMIT ?"
    )
    .all(teamId, limit);
}

function getWeekStatus(teamId, dateStr) {
  const range = getWeekRangeForDate(dateStr);
  if (!range) return null;
  const { weekStart, weekEnd } = range;
  const memberCount = db
    .prepare("SELECT COUNT(*) as count FROM members WHERE team_id = ?")
    .get(teamId).count;
  const totalCheckins = db
    .prepare(
      "SELECT COUNT(*) as count FROM checkins WHERE team_id = ? AND date BETWEEN ? AND ?"
    )
    .get(teamId, weekStart, weekEnd).count;
  const requiredTotal = memberCount * 3;
  const completionRate =
    requiredTotal === 0 ? 0 : Math.min(1, totalCheckins / requiredTotal);
  return {
    weekStart,
    weekEnd,
    memberCount,
    totalCheckins,
    requiredTotal,
    completionRate,
  };
}

function getMemberWeekStats(teamId, memberId, dateStr) {
  const range = getWeekRangeForDate(dateStr);
  if (!range) return null;
  const { weekStart, weekEnd } = range;
  const rows = db
    .prepare(
      "SELECT m.id, COALESCE(COUNT(c.id), 0) as count FROM members m LEFT JOIN checkins c ON c.member_id = m.id AND c.team_id = m.team_id AND c.date BETWEEN ? AND ? WHERE m.team_id = ? GROUP BY m.id"
    )
    .all(weekStart, weekEnd, teamId);
  if (!rows.length) return { weekStart, weekEnd, count: 0, totalMembers: 0, percentile: 0 };
  const current = rows.find((row) => row.id === memberId);
  if (!current) return null;
  const totalMembers = rows.length;
  const less = rows.filter((row) => row.count < current.count).length;
  const percentile = totalMembers === 0 ? 0 : Math.round((less / totalMembers) * 100);
  return { weekStart, weekEnd, count: current.count, totalMembers, percentile };
}

init();

module.exports = {
  listTeams,
  getTeam,
  createTeam,
  listMembers,
  getMember,
  createMember,
  createCheckin,
  addCheckinPhotos,
  listCheckins,
  getTeamStats,
  getLeaderboard,
  createChallenge,
  listChallenges,
  listMemberBadges,
  maybeAwardBadges,
  settleWeek,
  listWeeklySummaries,
  listLedger,
  getWeekStatus,
  getMemberWeekStats,
  formatDate,
  formatLocalDate,
  getWeekRangeForDate,
};
