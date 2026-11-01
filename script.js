const form = document.getElementById("form");
const btn = document.getElementById("btn");
const errorEl = document.getElementById("error");
const results = document.getElementById("results");

function fillChips(id, words) {
  const el = document.getElementById(id);
  el.innerHTML = "";
  if (!words.length) {
    el.textContent = "None";
    return;
  }
  words.forEach((w) => {
    const span = document.createElement("span");
    span.className = "chip";
    span.textContent = w;
    el.appendChild(span);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.hidden = true;
  results.hidden = true;
  btn.disabled = true;
  btn.textContent = "Analyzing...";

  try {
    const res = await fetch("/analyze", { method: "POST", body: new FormData(form) });
    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.error || "Something went wrong.";
      errorEl.hidden = false;
      return;
    }

    document.getElementById("score").textContent = data.score;
    document.getElementById("similarity").textContent = data.similarity;
    document.getElementById("coverage").textContent = data.coverage;
    fillChips("matched", data.matched);
    fillChips("missing", data.missing);

    const tips = document.getElementById("tips");
    tips.innerHTML = "";
    data.tips.forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      tips.appendChild(li);
    });

    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    errorEl.textContent = "Could not reach the server.";
    errorEl.hidden = false;
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze";
  }
});
