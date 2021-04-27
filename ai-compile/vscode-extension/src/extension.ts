import * as vscode from 'vscode';
import { compile, getFix, LocalStorage } from './util';
import { CodelensProvider } from './code-lens/codeLensProvider';

import * as t from './types';
import * as c from './constants';

let disposables: vscode.Disposable[] = [];
let eventDisposables: vscode.Disposable[] = [];

// file-wise history store
export let storageManager: LocalStorage;

async function compileAndGetFixHelper(
): Promise<t.Fix> {
	
	const activeEditor = vscode.window.activeTextEditor;

	if( activeEditor !== undefined ) {
		const document = activeEditor.document;
		const cursorPosition = activeEditor.selection.active;
		const filePath = document.uri.fsPath;
		let result: t.Fix = undefined;

		if( c.DEBUG ) {
			console.log( `Compiling ${filePath}` );
		}
		const compiled = await compile( filePath );

		if ( !compiled ) {
			if( c.DEBUG ) {
				console.log( "Syntax Error -> Preparing and Sending data..." );
			}
			const data: t.Payload = {
				source: document.getText(),
				lastEditLine: cursorPosition.line
			};
			const payload: t.Payload = JSON.parse( JSON.stringify( data ) );

			if( c.baseURL === undefined ) {
				console.log( "Web Server path invalid" );
				return undefined;
			}
			else {
				result = await getFix( c.baseURL!, payload );
				if( result !== undefined ) {
					if( c.DEBUG ) {
						console.log( "Reply from Server:" );
					}
				}
			}
		}

		return result;
	}
}


async function compileAndGetFix(
	document: vscode.TextDocument,
	storageManager: LocalStorage
): Promise<t.Fix> {
	
	const filePath = document.uri.fsPath;
	let fixes: t.Fix = undefined;
	let docHistory = storageManager.getValue<t.DocumentStore>( filePath );

	// compile if file has either not been examined previously (in the history of the extension) ||
	// it has been modified
	let compileFlag = docHistory === undefined || document.isDirty;

	docHistory = docHistory?? { filePath: filePath, fixes: fixes };

	if( compileFlag ) {
		fixes = await compileAndGetFixHelper();
		docHistory.fixes = fixes;
		storageManager.setValue<t.DocumentStore>( filePath, docHistory );
	} else {
		fixes = docHistory.fixes;
		if( fixes !== undefined ) {
			if( c.DEBUG ) {
				console.log( "Saved fixes from History:" );
			}
		}
	}

	return fixes;
}


function suggestFixes(
	fixes: t.Fix
): void {

	if( fixes === undefined ) {
		if( c.DEBUG ) {
			console.log( "Nothing to show" );
		}
	} else {
		if( c.DEBUG ) {
			console.log( fixes );
		}
	}

}


export function activate( context: vscode.ExtensionContext ) {

	if( c.DEBUG ) {
		console.log( "Extension 'python-hints' is now active!" );
	}

	storageManager = new LocalStorage( context.globalState );

	disposables.push( vscode.commands.registerCommand( 'python-hints.getFix', async function () {
		if( c.DEBUG ) {
			console.log( "getFix Command triggered..." );
		}
		const activeEditor = vscode.window.activeTextEditor;
		if( activeEditor !== undefined ) {
			const fixes = await compileAndGetFix( activeEditor.document, storageManager );
			suggestFixes( fixes );
		}
	}));

	eventDisposables.push( vscode.workspace.onWillSaveTextDocument( async saveEvent =>  {
		if( c.DEBUG ) {
			console.log( "Document Saved..." );
		}
		if( saveEvent.reason === vscode.TextDocumentSaveReason.Manual ) {
			const fixes = await compileAndGetFix( saveEvent.document, storageManager );
			suggestFixes( fixes );
		}
	}));

	disposables.push( vscode.languages.registerCodeLensProvider( "python", new CodelensProvider() ) );

    disposables.push( vscode.commands.registerCommand( "python-hints.enableCodeLens", () => {
        vscode.workspace.getConfiguration( "python-hints" ).update( "enableCodeLens", true, true );
    } ) );

    disposables.push( vscode.commands.registerCommand( "python-hints.disableCodeLens", () => {
        vscode.workspace.getConfiguration( "python-hints" ).update( "enableCodeLens", false, true );
    } ) );

    disposables.push( vscode.commands.registerCommand( "python-hints.codelensAction", () => {
        vscode.window.showInformationMessage( "CodeLens action clicked" );
    } ) );

	disposables.forEach( item => context.subscriptions.push( item ) );

	eventDisposables.forEach( item => context.subscriptions.push( item ) );

}


export function deactivate() {

	if( disposables ) {
		disposables.forEach( item => item.dispose() );
	}
	if( eventDisposables ) {
		eventDisposables.forEach( item => item.dispose() );
	}

    disposables = [];
	eventDisposables = [];

}
