import * as assert from 'assert';
import * as path from 'path';
import * as vscode from 'vscode';

const testFolderLocation = '/../../../../samples/';
// Need to search for the extension using publisher_name.extension_name.
// Will need to change this later
const extensionUri = 'undefined_publisher.python-tutor';

suite('Pytutor features tests', () => {

  
  test('should activate on opening a python file', async () => {
    // Load the rainfall problem file
    const uri = vscode.Uri.file(
      path.join(__dirname + testFolderLocation + 'rainfall.py')
    );
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document);
    await sleep(2000);

    
    const extension = vscode.extensions.getExtension(extensionUri);
    
    // Check if the pytutor extension is active
    assert(extension?.isActive);
  });

  test('should generate 3 diagnostics for rainfall problem', async () => {
    // Load the rainfall problem file
    const uri = vscode.Uri.file(
      path.join(__dirname + testFolderLocation + 'rainfall.py')
    );
    const document = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(document);
    await sleep(500);
    editor.document.save();
    // Need longer wait time since the server takes longer to respond for the first request.
    await sleep(10000);

    let diagnostics = vscode.languages.getDiagnostics(uri);
    
    // Should return 3 diagnostics
    assert(diagnostics.length === 3);
  });

});

// Used in some test cases to wait for the files to load
async function sleep(ms: number): Promise<void> {
	return new Promise(resolve => {
		setTimeout(resolve, ms);
	});
}
