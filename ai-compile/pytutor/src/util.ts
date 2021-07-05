import * as vscode from 'vscode';
import { promisify } from 'util';
import { exec } from 'child_process';
import { tmpdir } from 'os';
import { join } from 'path';

export const BEGINNER = 1;
export const EXPERT = 2;
export const MODE_MEMENTO_NAME = "Python_Tutor_Mode";
export const EXTENSION_NAME = "Python Tutor";
export const BEGINNER_ICON = '👩‍🎓';
export const EXPERT_ICON = '🚀';
export const TEMP_FILE_NAME = 'temp.py'

const fs = require('fs').promises;
const COMPILE_TIMEOUT = 100000;

export enum Modes {
	Beginner = BEGINNER,
	Expert = EXPERT
}

export function getModeIcon(mode: number) {
	if (mode === Modes.Beginner) {
		return BEGINNER_ICON;
	}
	else {
		return EXPERT_ICON
	}
}

export async function compiles(pythonPath: string): Promise<boolean> {
	let currentCodeSnapshot = vscode.window.activeTextEditor?.document.getText();
	let tempFilePath = join(tmpdir(), TEMP_FILE_NAME);
	
	await fs.writeFile(tempFilePath, currentCodeSnapshot);
	try {
		const execute = promisify(exec);
		await execute(
			`"${pythonPath}" -m py_compile "${tempFilePath}"`,
			{
				windowsHide: true,
				timeout: COMPILE_TIMEOUT,
			}
		);
	} catch (exception) {
		console.debug("Compilation failed: " + exception['message']);
		return false;
	}
	console.debug("Compiled successfully.")
	return true;
}