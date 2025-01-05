const vscode = require("vscode");

function activate(context) {
  console.log("Composer Injector extension is active!");

  // Register the submit command
  const submitDisposable = vscode.commands.registerCommand(
    "composerInjector.submit",
    async () => {
      try {
        // Open DevTools to get access to the webview context
        await vscode.commands.executeCommand(
          "workbench.action.webview.openDeveloperTools"
        );

        // The exact script that we know works
        const script = `
          Array.from(document.querySelectorAll('.composer-bar-button')).map(b => ({
              text: b.textContent,
              html: b.outerHTML
          }));

          const submitButton = Array.from(document.querySelectorAll('.composer-bar-button')).find(b => 
              b.textContent.toLowerCase().includes('submit')
          );
          
          submitButton?.click();
        `;

        // Execute the script
        eval(script);
      } catch (error) {
        console.error("Error:", error);
        vscode.window.showErrorMessage(`Failed: ${error.message}`);
      }
    }
  );

  context.subscriptions.push(submitDisposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
