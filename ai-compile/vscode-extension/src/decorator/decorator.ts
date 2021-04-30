import * as vscode from 'vscode';
import * as t from "../types";
import { storageManager } from '../extension';

// export class FileDecorationProvider implements vscode.FileDecorationProvider {

//     private regex: RegExp;
//     private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
//     public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;

// 	constructor() {
// 		this.regex = /(.+)/g;
// 	}

// 	public provideFileDecoration( uri: vscode.Uri, token: vscode.CancellationToken ): vscode.Decora {

// 	}
// }


export class Decorator {

	private decorationType: vscode.TextEditorDecorationType;
	private eventDisposables: vscode.Disposable[] = [];
	private regEx;

	constructor() {
		// create a decorator type that we use to decorate small numbers
		this.decorationType = vscode.window.createTextEditorDecorationType({
			borderWidth: '1px',
			borderStyle: 'solid',
			overviewRulerColor: 'blue',
			overviewRulerLane: vscode.OverviewRulerLane.Right,
			light: {
				// this color will be used in light color themes
				borderColor: 'darkblue',
				backgroundColor: 'lightblue'
			},
			dark: {
				// this color will be used in dark color themes
				borderColor: 'lightblue',
				backgroundColor: 'darkblue'
			}
		});
		this.regEx = /(.+)/g;
	}

	public updateDecorations() {

		const activeEditor = vscode.window.activeTextEditor;
		if (!activeEditor) {
			return;
		}

		const document = activeEditor.document;
		const filePath = document.uri.fsPath;
		const highlights: vscode.DecorationOptions[] = [];
		
		const decoratorFlag: boolean = vscode.workspace.getConfiguration( "python-hints" ).get( "activeHighlight", false );
		// console.log( "Updating decorations: " + flag );
		if( decoratorFlag ) {
			const diagnosticLevel: number = vscode.workspace.getConfiguration( "python-hints" ).get( "diagnosticLevel", 0 );
			const fixes: t.Fix = storageManager.getValue<t.DocumentStore>( filePath )?.fixes;
			fixes?.forEach( fix => {
				const position = new vscode.Position( fix.lineNo, 0 );
				let range = document.getWordRangeAtPosition( position, new RegExp( this.regEx ) );
				let diagnosticMsg: string = "";
				switch( diagnosticLevel ) {
					case 1: {
						diagnosticMsg = fix.feedbacks;
						break;
					}
					case 2: {
						diagnosticMsg = fix.repairClasses;
						break;
					}
					case 3: {
						// TODO: Token insertion/ deletion position
						// range = ;
						diagnosticMsg = fix.feedbacks;
						break;
					}
					case 4: {
						// already available in codelens
						diagnosticMsg = fix.repairLine;
					}
				}
				
				const decoration = { range: range!, hoverMessage: diagnosticMsg };
				highlights.push( decoration );
			} );
		}
		
		activeEditor.setDecorations( this.decorationType, highlights );

	}


	// this method is called when vs code is activated
	public registerDecorator( context: vscode.ExtensionContext ) {

		this.eventDisposables.push( vscode.window.onDidChangeActiveTextEditor( editor => {
			if( editor ) {
				this.updateDecorations();
			}
		}, null, context.subscriptions) );

		this.eventDisposables.push( vscode.workspace.onDidChangeTextDocument( event => {
			const activeEditor = vscode.window.activeTextEditor;
			if( activeEditor && event.document === activeEditor.document ) {
				this.updateDecorations();
			}
		}, null, context.subscriptions) );

	}


	// TODO: Maintain a state of all open editors?
	// Check Deregister of event disposables
	public deregisterDecorator( context: vscode.ExtensionContext ) {

		// this.registerDecorator( context, false );
		// vscode.workspace.getConfiguration( "python-hints" ).update( "activeHighlight", false, true );

	// 	if( this.eventDisposables ) {
	// 		this.eventDisposables.forEach( item => item.dispose() );
	// 	}

	// 	const activeEditor = vscode.window.activeTextEditor;

	// 	if( activeEditor ) {
	// 		activeEditor.setDecorations( this.decorationType, highlights );
	// 	}

	// 	this.eventDisposables = [];

	}
}
