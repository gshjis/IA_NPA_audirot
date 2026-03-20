import { useState, useRef, useEffect } from "react";
import { Icon } from "../icons/Icon";
import styles from "./FileUploadCard.module.css";

const ACCEPT = ".pdf,.docx";

type FileUploadCardProps = {
  title: string;
  description: string;
  icon: React.ReactNode;
  file: File | null;
  onFileChange: (file: File | null) => void;
  hasError?: boolean;
};

function getFileExt(file: File) {
  return file.name.split(".").pop()?.toLowerCase() ?? "";
}

export function FileUploadCard({
  title,
  description,
  icon,
  file,
  onFileChange,
  hasError = false,
}: FileUploadCardProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      queueMicrotask(() => setPreviewUrl(url));
      return () => URL.revokeObjectURL(url);
    }
    queueMicrotask(() => setPreviewUrl(null));
    return () => {};
  }, [file]);

  useEffect(() => {
    if (!file && inputRef.current) {
      inputRef.current.value = "";
    }
  }, [file]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      const ext = getFileExt(selected);
      if (ext === "pdf" || ext === "docx") {
        onFileChange(selected);
      }
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onFileChange(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const isPdf = file && getFileExt(file) === "pdf";

  return (
    <div className={styles.wrapper}>
      <h3 className={styles.cardTitle}>{title}</h3>
      <p className={styles.cardDesc}>{description}</p>
      <label
        className={`${styles.uploadCard} ${hasError ? styles.uploadCardError : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={handleChange}
          className={styles.fileInput}
        />
        {file ? (
          <div className={styles.fileInfo}>
            <div className={styles.previewArea}>
              {isPdf && previewUrl ? (
                <iframe
                  src={previewUrl}
                  title={file.name}
                  className={styles.previewFrame}
                />
              ) : (
                <div className={styles.docxPlaceholder}>
                  <Icon name="file-doc" size={48} />
                  <span className={styles.docxExt}>DOCX</span>
                </div>
              )}
            </div>
            <div className={styles.fileBar}>
              <span className={styles.fileName} title={file.name}>
                {file.name}
              </span>
              <button
                type="button"
                className={styles.removeBtn}
                onClick={handleRemove}
                aria-label="Удалить файл"
              >
                <Icon name="x" size={16} />
              </button>
            </div>
            <span className={styles.replaceHint}>Нажмите, чтобы заменить</span>
          </div>
        ) : (
          <>
            <div className={styles.iconCircle}>{icon}</div>
            <span className={styles.fileLabel}>
              <Icon name="clip" size={16} />
              Выбрать файл
            </span>
          </>
        )}
      </label>
    </div>
  );
}
