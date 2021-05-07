export interface Payload {
  source: string;
  lastEditLine: number;
}



export interface Edit {
  type: string;
  start: number;
  end: number;
  insertString: string;
}

export interface Response {
  lineNo: number;
  repairLine: string;
  feedbacks: string;
  repairClasses: string;
  editDiffs: Edit[];
}

export interface DocumentStore {
  // TODO: Can this be made private? Does it make sense?
  filePath: string;
  fixes: Fix;
}

export type Fix = Response[] | undefined;
