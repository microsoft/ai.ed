export interface Payload {
  source: string;
  lastEditLine: number;
}

export interface Response {
  lineNo: number;
  repairLine: string;
  feedbacks: string;
  repairClasses: string;
}

export interface DocumentStore {
  // TODO: Can this be made private? Does it make sense?
  filePath: string;
  fixes: Fix;
}

export type Fix = Response[] | undefined;
