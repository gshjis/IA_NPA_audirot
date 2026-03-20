export type UploadAndCompareResponse = {
  analysis_id: string;
  status: string;
  old_document: {
    document_id: string;
    filename: string;
    uploaded_at: string;
  };
  new_document: {
    document_id: string;
    filename: string;
    uploaded_at: string;
  };
};
