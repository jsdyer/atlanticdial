const el = id => document.getElementById(id);
const county = row => row.place.split(",").at(-2).trim();
function normalize(input) {
  return input.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().replace(/[’']/g, "")
    .replace(/south[- ]east passage|eastern passage/g, "eastern passage")
    .replace(/musduodoboit/g, "musquodoboit");
}
export function findRecordings(recordings, query, selectedCounty) {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  return recordings.filter(row => {
    if (selectedCounty && county(row) !== selectedCounty) return false;
    const text = normalize([row.title, ...(row.otherTitles || []), row.performer, row.place,
      row.year, "Reel " + row.reel, "Recording " + row.number].join(" "));
    return words.every(word => text.includes(word));
  });
}

function entry(row) {
  const article = document.createElement("article");
  article.className = "episode";
  const reference = document.createElement("span");
  reference.className = "recording-cue";
  reference.textContent = row.year + " · Reel " + row.reel + " · " + row.cue;
  const body = document.createElement("div");
  const title = document.createElement("h3");
  const link = document.createElement("a");
  link.href = row.url;
  link.textContent = row.title;
  title.append(link);
  const performer = document.createElement("p");
  performer.textContent = row.performer + " · " + row.place;
  const number = document.createElement("p");
  number.className = "recording-cue";
  number.textContent = "Recording " + row.number;
  body.append(title, performer, number);
  article.append(reference, body);
  return article;
}
export async function setupRecordings() {
  const summary = el("recording-summary");
  try {
    const response = await fetch("./recordings.json");
    if (!response.ok) throw Error();
    const {recordings} = await response.json();
    const counties = [...new Set(recordings.map(county))].sort();
    const years = recordings.map(row => row.year);
    const reels = new Set(recordings.map(row => row.reel));
    el("reel-edition").textContent = Math.min(...years) + "–" + Math.max(...years) + " · " + reels.size + " archival reels";
    const select = el("recording-county");
    for (const name of counties) select.add(new Option(name, name));
    let limit = 12;
    function render() {
      const rows = findRecordings(recordings, el("recording-search").value, select.value);
      const shown = rows.slice(0, limit);
      summary.textContent = rows.length ? shown.length + " of " + rows.length + " recordings" : "No matching recordings. Try another name or county.";
      el("recording-list").replaceChildren(...shown.map(entry));
      el("more-recordings").hidden = shown.length === rows.length;
    }
    function reset() { limit = 12; render(); }
    el("recording-search").addEventListener("input", reset);
    select.addEventListener("change", reset);
    el("more-recordings").addEventListener("click", () => {
      const previous = limit;
      limit += 12;
      render();
      el("recording-list").children[previous]?.querySelector("a")?.focus({preventScroll: true});
    });
    render();
  } catch {
    summary.textContent = "The local recording index could not load. Open the complete collection below.";
  }
}
