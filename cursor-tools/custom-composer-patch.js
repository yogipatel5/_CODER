(function () {
  document.addEventListener("DOMContentLoaded", () => {
    // Select the editor container
    const editorContainer = document.querySelector(".editor-container");

    if (editorContainer) {
      // Add a test message to the editor container
      const message = document.createElement("div");
      message.textContent = "Hello from Monkey Patch!";
      message.style.padding = "10px";
      message.style.backgroundColor = "#ffdd57";
      message.style.color = "#333";
      message.style.fontWeight = "bold";

      // Append the message to the editor container
      editorContainer.appendChild(message);

      console.log("Monkey Patch: Message injected into the editor container.");
    } else {
      console.warn("Monkey Patch: Editor container not found.");
    }
  });
})();
