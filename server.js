const path = require("path");
const fs = require("fs");
const express = require("express");
const multer = require("multer");
const db = require("./db");

const app = express();
const PORT = process.env.PORT || 3000;

const dataDir = process.env.DATA_DIR || __dirname;
const uploadRoot = path.join(dataDir, "uploads");
fs.mkdirSync(uploadRoot, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const month = new Date().toISOString().slice(0, 7).replace("-", "");
    const targetDir = path.join(uploadRoot, month);
    fs.mkdirSync(targetDir, { recursive: true });
    cb(null, targetDir);
  },
  filename: (req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._-]/g, "");
    const unique = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}-${safeName}`;
    cb(null, unique);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024, files: 6 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype && file.mimetype.startsWith("image/")) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed"));
    }
  },
});

app.use(express.json({ limit: "1mb" }));
app.use("/uploads", express.static(uploadRoot));
app.use(express.static(path.join(__dirname, "public")));

function isValidName(value) {
  return (
    typeof value === "string" && value.trim().length >= 1 && value.trim().length <= 60
  );
}

function isValidDate(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function toInt(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function today() {
  return db.formatLocalDate(new Date());
}

app.get("/api/health", (req, res) => {
  res.json({ ok: true });
});

app.get("/api/teams", (req, res) => {
  res.json(db.listTeams());
});

app.post("/api/teams", (req, res) => {
  const name = req.body?.name;
  if (!isValidName(name)) {
    return res.status(400).json({ error: "Invalid team name" });
  }
  const team = db.createTeam(name.trim());
  return res.status(201).json(team);
});

app.get("/api/teams/:teamId/members", (req, res) => {
  const teamId = toInt(req.params.teamId);
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.listMembers(teamId));
});

app.post("/api/teams/:teamId/members", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const name = req.body?.name;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  if (!isValidName(name)) {
    return res.status(400).json({ error: "Invalid member name" });
  }
  const member = db.createMember(teamId, name.trim());
  return res.status(201).json(member);
});

app.get("/api/teams/:teamId/checkins", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const date = req.query.date;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (date && !isValidDate(date)) {
    return res.status(400).json({ error: "Invalid date" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.listCheckins(teamId, date));
});

app.post(
  "/api/teams/:teamId/checkins",
  upload.array("photos", 6),
  (req, res) => {
    const teamId = toInt(req.params.teamId);
    const memberId = toInt(req.body?.memberId);
    const date = req.body?.date || today();
    const note = req.body?.note || "";

    if (!teamId || !memberId) {
      return res.status(400).json({ error: "Invalid team or member id" });
    }
    if (!isValidDate(date)) {
      return res.status(400).json({ error: "Invalid date" });
    }
    const member = db.getMember(memberId);
    if (!member || member.team_id !== teamId) {
      return res.status(400).json({ error: "Member does not belong to team" });
    }

    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ error: "Photo required" });
    }

    const result = db.createCheckin(teamId, memberId, date, note);
    if (!result.created) {
      return res.json({ created: false, reason: "duplicate" });
    }

    const photos = req.files.map((file) => {
      const rel = path.relative(uploadRoot, file.path);
      return `/uploads/${rel.replace(/\\/g, "/")}`;
    });
    db.addCheckinPhotos(result.checkin.id, photos);

    const badgesAwarded = db.maybeAwardBadges(memberId, date);
    return res.status(201).json({
      created: true,
      checkin: result.checkin,
      photos,
      badgesAwarded,
    });
  }
);

app.get("/api/teams/:teamId/summary", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const startDate = req.query.start;
  const endDate = req.query.end;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!isValidDate(startDate) || !isValidDate(endDate)) {
    return res.status(400).json({ error: "Invalid date range" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.getTeamStats(teamId, startDate, endDate));
});

app.get("/api/teams/:teamId/leaderboard", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const startDate = req.query.start;
  const endDate = req.query.end;
  const limit = toInt(req.query.limit) || 10;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!isValidDate(startDate) || !isValidDate(endDate)) {
    return res.status(400).json({ error: "Invalid date range" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.getLeaderboard(teamId, startDate, endDate, limit));
});

app.get("/api/teams/:teamId/challenges", (req, res) => {
  const teamId = toInt(req.params.teamId);
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.listChallenges(teamId));
});

app.post("/api/teams/:teamId/challenges", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const name = req.body?.name;
  const startDate = req.body?.startDate;
  const endDate = req.body?.endDate;
  const targetTotal = toInt(req.body?.targetTotal);

  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  if (!isValidName(name)) {
    return res.status(400).json({ error: "Invalid challenge name" });
  }
  if (!isValidDate(startDate) || !isValidDate(endDate)) {
    return res.status(400).json({ error: "Invalid date range" });
  }
  if (!targetTotal || targetTotal < 1) {
    return res.status(400).json({ error: "Invalid target total" });
  }

  const challenge = db.createChallenge(
    teamId,
    name.trim(),
    startDate,
    endDate,
    targetTotal
  );
  return res.status(201).json(challenge);
});

app.get("/api/members/:memberId/badges", (req, res) => {
  const memberId = toInt(req.params.memberId);
  if (!memberId) {
    return res.status(400).json({ error: "Invalid member id" });
  }
  if (!db.getMember(memberId)) {
    return res.status(404).json({ error: "Member not found" });
  }
  return res.json(db.listMemberBadges(memberId));
});

app.get("/api/teams/:teamId/weekly-status", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const date = req.query.date || today();
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!isValidDate(date)) {
    return res.status(400).json({ error: "Invalid date" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  const status = db.getWeekStatus(teamId, date);
  return res.json(status);
});

app.get("/api/teams/:teamId/member-weekly", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const memberId = toInt(req.query.memberId);
  const date = req.query.date || today();
  if (!teamId || !memberId) {
    return res.status(400).json({ error: "Invalid team or member id" });
  }
  if (!isValidDate(date)) {
    return res.status(400).json({ error: "Invalid date" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  const member = db.getMember(memberId);
  if (!member || member.team_id !== teamId) {
    return res.status(400).json({ error: "Member does not belong to team" });
  }
  const stats = db.getMemberWeekStats(teamId, memberId, date);
  return res.json(stats);
});

app.post("/api/teams/:teamId/weekly-settle", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const weekStart = req.body?.weekStart;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!isValidDate(weekStart)) {
    return res.status(400).json({ error: "Invalid week start" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  const result = db.settleWeek(teamId, weekStart);
  if (!result) {
    return res.status(400).json({ error: "Unable to settle week" });
  }
  return res.json(result);
});

app.get("/api/teams/:teamId/weekly-summaries", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const limit = toInt(req.query.limit) || 50;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.listWeeklySummaries(teamId, limit));
});

app.get("/api/teams/:teamId/ledger", (req, res) => {
  const teamId = toInt(req.params.teamId);
  const limit = toInt(req.query.limit) || 50;
  if (!teamId) {
    return res.status(400).json({ error: "Invalid team id" });
  }
  if (!db.getTeam(teamId)) {
    return res.status(404).json({ error: "Team not found" });
  }
  return res.json(db.listLedger(teamId, limit));
});

app.use((err, req, res, next) => {
  if (err) {
    return res.status(400).json({ error: err.message || "Upload error" });
  }
  return next();
});

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  // eslint-disable-next-line no-console
  console.log(`Server listening on http://localhost:${PORT}`);
});
