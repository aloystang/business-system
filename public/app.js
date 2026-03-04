const state = {
  teamId: null,
  memberId: null,
};

const els = {
  teamSelect: document.getElementById("teamSelect"),
  teamNameInput: document.getElementById("teamNameInput"),
  createTeamBtn: document.getElementById("createTeamBtn"),
  memberList: document.getElementById("memberList"),
  memberNameInput: document.getElementById("memberNameInput"),
  addMemberBtn: document.getElementById("addMemberBtn"),
  checkinMemberSelect: document.getElementById("checkinMemberSelect"),
  checkinDate: document.getElementById("checkinDate"),
  checkinNote: document.getElementById("checkinNote"),
  checkinPhotos: document.getElementById("checkinPhotos"),
  photoPreview: document.getElementById("photoPreview"),
  checkinBtn: document.getElementById("checkinBtn"),
  checkinHint: document.getElementById("checkinHint"),
  statsStart: document.getElementById("statsStart"),
  statsEnd: document.getElementById("statsEnd"),
  refreshStatsBtn: document.getElementById("refreshStatsBtn"),
  summary: document.getElementById("summary"),
  leaderboardList: document.getElementById("leaderboardList"),
  challengeList: document.getElementById("challengeList"),
  challengeEmpty: document.getElementById("challengeEmpty"),
  challengeNameInput: document.getElementById("challengeNameInput"),
  challengeStart: document.getElementById("challengeStart"),
  challengeEnd: document.getElementById("challengeEnd"),
  challengeTarget: document.getElementById("challengeTarget"),
  createChallengeBtn: document.getElementById("createChallengeBtn"),
  badgeMemberSelect: document.getElementById("badgeMemberSelect"),
  badgeList: document.getElementById("badgeList"),
  checkinFilterDate: document.getElementById("checkinFilterDate"),
  checkinList: document.getElementById("checkinList"),
  memberEmpty: document.getElementById("memberEmpty"),
  toast: document.getElementById("toast"),
  weekRange: document.getElementById("weekRange"),
  metricTotal: document.getElementById("metricTotal"),
  metricRate: document.getElementById("metricRate"),
  metricRequired: document.getElementById("metricRequired"),
  metricRemaining: document.getElementById("metricRemaining"),
  metricMemberLabel: document.getElementById("metricMemberLabel"),
  metricMemberCount: document.getElementById("metricMemberCount"),
  metricMemberPercent: document.getElementById("metricMemberPercent"),
  settleWeekStart: document.getElementById("settleWeekStart"),
  settleWeekBtn: document.getElementById("settleWeekBtn"),
  settleResult: document.getElementById("settleResult"),
  ledgerList: document.getElementById("ledgerList"),
  weeklyList: document.getElementById("weeklyList"),
};

const tabs = Array.from(document.querySelectorAll(".tab"));
const pages = Array.from(document.querySelectorAll(".page"));

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast.timeoutId);
  showToast.timeoutId = window.setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2200);
}

async function api(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

async function apiForm(path, formData) {
  const response = await fetch(path, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function getMonday(date) {
  const day = date.getDay();
  const diff = (day + 6) % 7;
  const monday = new Date(date);
  monday.setDate(date.getDate() - diff);
  return monday;
}

function setDefaultDates() {
  const today = new Date();
  els.checkinDate.value = formatDate(today);
  els.checkinFilterDate.value = formatDate(today);
  els.challengeStart.value = formatDate(today);
  const end = new Date(today);
  end.setDate(end.getDate() + 30);
  els.challengeEnd.value = formatDate(end);

  const start = new Date(today);
  start.setDate(start.getDate() - 6);
  els.statsStart.value = formatDate(start);
  els.statsEnd.value = formatDate(today);

  els.settleWeekStart.value = formatDate(getMonday(today));
}

function clearList(el) {
  while (el.firstChild) {
    el.removeChild(el.firstChild);
  }
}

function switchPage(target) {
  pages.forEach((page) => {
    page.classList.toggle("active", page.dataset.page === target);
  });
  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.target === target);
  });
  if (target) {
    window.location.hash = target;
  }
}

function updateMemberLabel() {
  const selected = els.checkinMemberSelect?.selectedOptions?.[0];
  if (selected) {
    els.metricMemberLabel.textContent = `当前成员 · ${selected.textContent}`;
  } else {
    els.metricMemberLabel.textContent = "当前成员";
  }
}

function renderMembers(members) {
  clearList(els.memberList);
  if (!members.length) {
    els.memberEmpty.textContent = "还没有成员。";
    els.memberEmpty.style.display = "block";
  } else {
    els.memberEmpty.style.display = "none";
  }

  members.forEach((member) => {
    const li = document.createElement("li");
    li.textContent = member.name;
    els.memberList.appendChild(li);
  });

  const selects = [els.checkinMemberSelect, els.badgeMemberSelect];
  selects.forEach((select) => {
    clearList(select);
    members.forEach((member) => {
      const option = document.createElement("option");
      option.value = member.id;
      option.textContent = member.name;
      select.appendChild(option);
    });
  });

  if (members.length) {
    state.memberId = members[0].id;
    els.checkinMemberSelect.value = String(state.memberId);
    els.badgeMemberSelect.value = String(state.memberId);
  } else {
    state.memberId = null;
  }

  updateMemberLabel();
}

function renderLeaderboard(rows) {
  clearList(els.leaderboardList);
  if (!rows.length) {
    const li = document.createElement("li");
    li.textContent = "还没有打卡记录。";
    els.leaderboardList.appendChild(li);
    return;
  }
  rows.forEach((row, index) => {
    const li = document.createElement("li");
    li.textContent = `${index + 1}. ${row.name} - ${row.checkins} 次打卡`;
    els.leaderboardList.appendChild(li);
  });
}

function renderChallenges(challenges) {
  els.challengeEmpty.style.display = challenges.length ? "none" : "block";
  els.challengeList.innerHTML = "";

  challenges.forEach((challenge) => {
    const wrapper = document.createElement("div");
    wrapper.style.marginBottom = "10px";

    const title = document.createElement("div");
    title.innerHTML = `<strong>${challenge.name}</strong> <span class="small">(${challenge.start_date} 至 ${challenge.end_date})</span>`;

    const progress = document.createElement("div");
    progress.className = "progress";
    const bar = document.createElement("span");
    const percent = Math.min(
      100,
      Math.round((challenge.progress / challenge.target_total) * 100)
    );
    bar.style.width = `${percent}%`;
    progress.appendChild(bar);

    const meta = document.createElement("div");
    meta.className = "small";
    meta.textContent = `${challenge.progress} / ${challenge.target_total} 次打卡 ${
      challenge.completed ? "(已完成)" : ""
    }`;

    wrapper.appendChild(title);
    wrapper.appendChild(progress);
    wrapper.appendChild(meta);
    els.challengeList.appendChild(wrapper);
  });
}

function renderBadges(badges) {
  clearList(els.badgeList);
  if (!badges.length) {
    const li = document.createElement("li");
    li.textContent = "还没有获得勋章。";
    els.badgeList.appendChild(li);
    return;
  }

  badges.forEach((badge) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="badge">${badge.name}</span> <span class="small">${badge.description}</span>`;
    els.badgeList.appendChild(li);
  });
}

function renderCheckins(checkins) {
  clearList(els.checkinList);
  if (!checkins.length) {
    const li = document.createElement("li");
    li.textContent = "暂无打卡记录。";
    els.checkinList.appendChild(li);
    return;
  }

  checkins.forEach((checkin) => {
    const li = document.createElement("li");
    li.className = "checkin-item";

    const title = document.createElement("div");
    title.className = "checkin-title";
    title.textContent = `${checkin.member_name} · ${checkin.date}`;

    const meta = document.createElement("div");
    meta.className = "checkin-meta";
    meta.textContent = checkin.note ? checkin.note : "无备注";

    const photos = document.createElement("div");
    photos.className = "checkin-photos";
    if (checkin.photos && checkin.photos.length) {
      checkin.photos.forEach((path) => {
        const img = document.createElement("img");
        img.src = path;
        img.alt = "打卡照片";
        photos.appendChild(img);
      });
    }

    li.appendChild(title);
    li.appendChild(meta);
    if (checkin.photos && checkin.photos.length) {
      li.appendChild(photos);
    }
    els.checkinList.appendChild(li);
  });
}

function renderWeeklyStatus(status) {
  if (!status) return;
  els.weekRange.textContent = `${status.weekStart} ~ ${status.weekEnd}`;
  els.metricTotal.textContent = status.totalCheckins;
  const rate = Math.round(status.completionRate * 100);
  els.metricRate.textContent = `${rate}%`;
  els.metricRequired.textContent = `需完成 ${status.requiredTotal} 次`;
  const remaining = Math.max(0, status.requiredTotal - status.totalCheckins);
  els.metricRemaining.textContent = remaining;
}

function renderMemberWeekly(stats) {
  if (!stats) {
    els.metricMemberCount.textContent = "本周打卡 0 次";
    els.metricMemberPercent.textContent = "超过 0% 的成员";
    return;
  }
  els.metricMemberCount.textContent = `本周打卡 ${stats.count} 次`;
  els.metricMemberPercent.textContent = `超过 ${stats.percentile}% 的成员`;
}

function renderSettleResults(results, weekRange) {
  clearList(els.settleResult);
  if (!results || !results.length) {
    const li = document.createElement("li");
    li.textContent = "暂无结算结果。";
    els.settleResult.appendChild(li);
    return;
  }
  results.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `${row.memberName} · 打卡 ${row.checkins} 次 · 缺口 ${row.missing} 次 · 扣款 ${row.penalty} 元`;
    els.settleResult.appendChild(li);
  });
  if (weekRange) {
    els.weekRange.textContent = weekRange;
  }
}

function renderLedger(rows) {
  clearList(els.ledgerList);
  if (!rows.length) {
    const li = document.createElement("li");
    li.textContent = "暂无扣款记录。";
    els.ledgerList.appendChild(li);
    return;
  }
  rows.forEach((row) => {
    const li = document.createElement("li");
    const amount = row.amount;
    li.textContent = `${row.member_name} · ${row.week_start} · ${amount} 元 · ${row.note || ""}`;
    els.ledgerList.appendChild(li);
  });
}

function renderWeeklySummaries(rows) {
  clearList(els.weeklyList);
  if (!rows.length) {
    const li = document.createElement("li");
    li.textContent = "暂无历史周报。";
    els.weeklyList.appendChild(li);
    return;
  }
  rows.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `${row.member_name} · ${row.week_start} ~ ${row.week_end} · 打卡 ${row.checkin_count} 次 · 缺口 ${row.missing_count} 次 · 扣款 ${row.penalty_amount} 元`;
    els.weeklyList.appendChild(li);
  });
}

function previewPhotos(files) {
  els.photoPreview.innerHTML = "";
  if (!files || files.length === 0) return;
  Array.from(files).forEach((file) => {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = "预览";
    els.photoPreview.appendChild(img);
  });
}

async function loadTeams() {
  const teams = await api("/api/teams");
  clearList(els.teamSelect);
  teams.forEach((team) => {
    const option = document.createElement("option");
    option.value = team.id;
    option.textContent = team.name;
    els.teamSelect.appendChild(option);
  });

  if (teams.length) {
    state.teamId = teams[0].id;
    els.teamSelect.value = String(state.teamId);
    await refreshTeamData();
  } else {
    state.teamId = null;
    renderMembers([]);
    renderLeaderboard([]);
    renderChallenges([]);
    renderBadges([]);
    renderCheckins([]);
    renderLedger([]);
    renderWeeklySummaries([]);
    els.summary.textContent = "先创建一个团队开始吧。";
    els.weekRange.textContent = "--";
    els.metricTotal.textContent = "0";
    els.metricRate.textContent = "0%";
    els.metricRequired.textContent = "需完成 0 次";
    els.metricRemaining.textContent = "0";
    els.metricMemberLabel.textContent = "当前成员";
    els.metricMemberCount.textContent = "本周打卡 0 次";
    els.metricMemberPercent.textContent = "超过 0% 的成员";
  }
}

async function refreshTeamData() {
  if (!state.teamId) return;
  const members = await api(`/api/teams/${state.teamId}/members`);
  renderMembers(members);
  await refreshStats();
  await refreshChallenges();
  await refreshBadges();
  await refreshCheckins();
  await refreshWeeklyStatus();
  await refreshMemberWeekly();
  await refreshLedger();
  await refreshWeeklySummaries();
}

async function refreshStats() {
  if (!state.teamId) return;
  const start = els.statsStart.value;
  const end = els.statsEnd.value;
  const summary = await api(
    `/api/teams/${state.teamId}/summary?start=${start}&end=${end}`
  );
  els.summary.textContent = `总打卡数：${summary.totalCheckins}。活跃成员：${summary.activeMembers}。`;
  const leaderboard = await api(
    `/api/teams/${state.teamId}/leaderboard?start=${start}&end=${end}&limit=10`
  );
  renderLeaderboard(leaderboard);
}

async function refreshChallenges() {
  if (!state.teamId) return;
  const challenges = await api(`/api/teams/${state.teamId}/challenges`);
  renderChallenges(challenges);
}

async function refreshBadges() {
  if (!state.memberId) {
    renderBadges([]);
    return;
  }
  const badges = await api(`/api/members/${state.memberId}/badges`);
  renderBadges(badges);
}

async function refreshCheckins() {
  if (!state.teamId) return;
  const date = els.checkinFilterDate.value;
  const url = date
    ? `/api/teams/${state.teamId}/checkins?date=${date}`
    : `/api/teams/${state.teamId}/checkins`;
  const checkins = await api(url);
  renderCheckins(checkins);
}

async function refreshWeeklyStatus() {
  if (!state.teamId) return;
  const date = els.checkinDate.value || formatDate(new Date());
  const status = await api(
    `/api/teams/${state.teamId}/weekly-status?date=${date}`
  );
  renderWeeklyStatus(status);
}

async function refreshMemberWeekly() {
  if (!state.teamId || !state.memberId) {
    renderMemberWeekly(null);
    return;
  }
  const date = els.checkinDate.value || formatDate(new Date());
  const stats = await api(
    `/api/teams/${state.teamId}/member-weekly?memberId=${state.memberId}&date=${date}`
  );
  renderMemberWeekly(stats);
}

async function refreshLedger() {
  if (!state.teamId) return;
  const ledger = await api(`/api/teams/${state.teamId}/ledger?limit=30`);
  renderLedger(ledger);
}

async function refreshWeeklySummaries() {
  if (!state.teamId) return;
  const weekly = await api(`/api/teams/${state.teamId}/weekly-summaries?limit=30`);
  renderWeeklySummaries(weekly);
}

els.createTeamBtn.addEventListener("click", async () => {
  const name = els.teamNameInput.value.trim();
  if (!name) {
    showToast("请输入团队名称。");
    return;
  }
  await api("/api/teams", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  els.teamNameInput.value = "";
  showToast("团队已创建。");
  await loadTeams();
});

els.teamSelect.addEventListener("change", async (event) => {
  state.teamId = Number(event.target.value);
  await refreshTeamData();
});

els.addMemberBtn.addEventListener("click", async () => {
  if (!state.teamId) {
    showToast("请先选择一个团队。");
    return;
  }
  const name = els.memberNameInput.value.trim();
  if (!name) {
    showToast("请输入成员姓名。");
    return;
  }
  await api(`/api/teams/${state.teamId}/members`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  els.memberNameInput.value = "";
  showToast("成员已添加。");
  await refreshTeamData();
});

els.checkinMemberSelect.addEventListener("change", () => {
  state.memberId = Number(els.checkinMemberSelect.value);
  els.badgeMemberSelect.value = String(state.memberId);
  updateMemberLabel();
  refreshBadges();
  refreshMemberWeekly();
});

els.badgeMemberSelect.addEventListener("change", () => {
  state.memberId = Number(els.badgeMemberSelect.value);
  els.checkinMemberSelect.value = String(state.memberId);
  updateMemberLabel();
  refreshBadges();
  refreshMemberWeekly();
});

els.checkinPhotos.addEventListener("change", () => {
  previewPhotos(els.checkinPhotos.files);
});

els.checkinDate.addEventListener("change", async () => {
  await refreshWeeklyStatus();
  await refreshMemberWeekly();
});

els.checkinBtn.addEventListener("click", async () => {
  if (!state.teamId || !state.memberId) {
    showToast("请先选择团队和成员。");
    return;
  }
  const date = els.checkinDate.value;
  const note = els.checkinNote.value.trim();
  const files = els.checkinPhotos.files;
  if (!files || files.length === 0) {
    showToast("请上传至少一张照片。");
    return;
  }

  const formData = new FormData();
  formData.append("memberId", state.memberId);
  formData.append("date", date);
  formData.append("note", note);
  Array.from(files).forEach((file) => {
    formData.append("photos", file);
  });

  const response = await apiForm(`/api/teams/${state.teamId}/checkins`, formData);

  if (!response.created) {
    showToast("该日期已打卡。");
    return;
  }

  if (response.badgesAwarded && response.badgesAwarded.length) {
    els.checkinHint.textContent = `获得勋章：${response.badgesAwarded
      .map((badge) => badge.name)
      .join(", ")}`;
  } else {
    els.checkinHint.textContent = "";
  }

  els.checkinNote.value = "";
  els.checkinPhotos.value = "";
  els.photoPreview.innerHTML = "";
  showToast("打卡已记录。");
  await refreshTeamData();
});

els.refreshStatsBtn.addEventListener("click", async () => {
  await refreshStats();
});

els.createChallengeBtn.addEventListener("click", async () => {
  if (!state.teamId) {
    showToast("请先选择一个团队。");
    return;
  }
  const name = els.challengeNameInput.value.trim();
  const startDate = els.challengeStart.value;
  const endDate = els.challengeEnd.value;
  const targetTotal = Number(els.challengeTarget.value);

  if (!name || !startDate || !endDate || !targetTotal) {
    showToast("请填写完整的挑战信息。");
    return;
  }

  await api(`/api/teams/${state.teamId}/challenges`, {
    method: "POST",
    body: JSON.stringify({ name, startDate, endDate, targetTotal }),
  });

  els.challengeNameInput.value = "";
  els.challengeTarget.value = "";
  showToast("挑战已创建。");
  await refreshChallenges();
});

els.checkinFilterDate.addEventListener("change", async () => {
  await refreshCheckins();
});

els.settleWeekBtn.addEventListener("click", async () => {
  if (!state.teamId) {
    showToast("请先选择一个团队。");
    return;
  }
  const weekStart = els.settleWeekStart.value;
  if (!weekStart) {
    showToast("请选择周一日期。");
    return;
  }
  const result = await api(`/api/teams/${state.teamId}/weekly-settle`, {
    method: "POST",
    body: JSON.stringify({ weekStart }),
  });
  renderSettleResults(result.results, `${result.weekStart} ~ ${result.weekEnd}`);
  await refreshLedger();
  await refreshWeeklySummaries();
  showToast("结算已生成。");
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    switchPage(tab.dataset.target);
  });
});

window.addEventListener("load", async () => {
  const hash = window.location.hash.replace("#", "");
  switchPage(hash || "checkin");
  setDefaultDates();
  try {
    await loadTeams();
  } catch (err) {
    showToast("加载数据失败。");
  }
});
