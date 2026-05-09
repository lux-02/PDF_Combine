const files = [];

const fileInput = document.querySelector("#fileInput");
const fileList = document.querySelector("#fileList");
const emptyState = document.querySelector("#emptyState");
const summary = document.querySelector("#summary");
const clearButton = document.querySelector("#clearButton");
const sortAscButton = document.querySelector("#sortAscButton");
const sortDescButton = document.querySelector("#sortDescButton");
const combineButton = document.querySelector("#combineButton");
const filenameInput = document.querySelector("#filenameInput");
const resultText = document.querySelector("#resultText");
const dropzone = document.querySelector("#dropzone");

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function normalizeFilename(value) {
  const trimmed = value.trim() || "combined.pdf";
  return trimmed.toLowerCase().endsWith(".pdf") ? trimmed : `${trimmed}.pdf`;
}

function updateState() {
  const count = files.length;
  const totalBytes = files.reduce((sum, item) => sum + item.file.size, 0);

  summary.textContent = count ? `${count}개 파일 · ${formatBytes(totalBytes)}` : "0개 파일";
  emptyState.hidden = count > 0;
  clearButton.disabled = count === 0;
  sortAscButton.disabled = count < 2;
  sortDescButton.disabled = count < 2;
  combineButton.disabled = count === 0;

  fileList.replaceChildren();
  files.forEach((item, index) => {
    const row = document.createElement("li");
    row.className = "file-row";
    row.draggable = true;
    row.dataset.index = String(index);

    const meta = document.createElement("div");
    meta.className = "file-meta";

    const order = document.createElement("strong");
    order.textContent = String(index + 1);

    const text = document.createElement("div");
    const name = document.createElement("span");
    name.textContent = item.file.name;
    const size = document.createElement("small");
    size.textContent = formatBytes(item.file.size);
    text.append(name, size);
    meta.append(order, text);

    const actions = document.createElement("div");
    actions.className = "row-actions";
    actions.append(
      makeIconButton("↑", "위로", () => moveFile(index, index - 1), index === 0),
      makeIconButton("↓", "아래로", () => moveFile(index, index + 1), index === files.length - 1),
      makeIconButton("×", "삭제", () => removeFile(index), false)
    );

    row.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", String(index));
      row.classList.add("dragging");
    });
    row.addEventListener("dragend", () => row.classList.remove("dragging"));
    row.addEventListener("dragover", (event) => event.preventDefault());
    row.addEventListener("drop", (event) => {
      event.preventDefault();
      const fromIndex = Number(event.dataTransfer.getData("text/plain"));
      moveFile(fromIndex, index);
    });

    row.append(meta, actions);
    fileList.append(row);
  });
}

function makeIconButton(icon, label, onClick, disabled) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "icon-button";
  button.textContent = icon;
  button.ariaLabel = label;
  button.title = label;
  button.disabled = disabled;
  button.addEventListener("click", onClick);
  return button;
}

function addFiles(selectedFiles) {
  Array.from(selectedFiles)
    .filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"))
    .forEach((file) => files.push({ id: crypto.randomUUID(), file }));
  resultText.textContent = "";
  updateState();
}

function moveFile(fromIndex, toIndex) {
  if (toIndex < 0 || toIndex >= files.length || fromIndex === toIndex) return;
  const [item] = files.splice(fromIndex, 1);
  files.splice(toIndex, 0, item);
  resultText.textContent = "";
  updateState();
}

function removeFile(index) {
  files.splice(index, 1);
  resultText.textContent = "";
  updateState();
}

async function combineFiles() {
  combineButton.disabled = true;
  resultText.textContent = "처리 중";

  try {
    if (!window.PDFLib) {
      throw new Error("PDF 처리 모듈을 불러오지 못했습니다.");
    }

    const mergedPdf = await PDFLib.PDFDocument.create();
    for (const item of files) {
      const sourceBytes = await item.file.arrayBuffer();
      const sourcePdf = await PDFLib.PDFDocument.load(sourceBytes, { ignoreEncryption: false });
      const pageIndexes = sourcePdf.getPageIndices();
      const copiedPages = await mergedPdf.copyPages(sourcePdf, pageIndexes);
      copiedPages.forEach((page) => mergedPdf.addPage(page));
    }

    const mergedBytes = await mergedPdf.save();
    const blob = new Blob([mergedBytes], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = normalizeFilename(filenameInput.value);
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    resultText.textContent = `완료 · ${formatBytes(blob.size)}`;
  } catch (error) {
    resultText.textContent = error.message;
  } finally {
    combineButton.disabled = files.length === 0;
  }
}

fileInput.addEventListener("change", (event) => {
  addFiles(event.target.files);
  fileInput.value = "";
});

clearButton.addEventListener("click", () => {
  files.splice(0, files.length);
  resultText.textContent = "";
  updateState();
});

function compareFileNames(a, b) {
  return a.file.name.localeCompare(b.file.name, "ko", { numeric: true });
}

sortAscButton.addEventListener("click", () => {
  files.sort(compareFileNames);
  resultText.textContent = "";
  updateState();
});

sortDescButton.addEventListener("click", () => {
  files.sort((a, b) => compareFileNames(b, a));
  resultText.textContent = "";
  updateState();
});

combineButton.addEventListener("click", combineFiles);

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  addFiles(event.dataTransfer.files);
});

updateState();
