import { useState } from 'react';
import { Upload, Download, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import api from '../../utils/api';

const BulkUpload = ({ entity, uploadEndpoint, templateEndpoint }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [downloadError, setDownloadError] = useState(null);

  const handleDownload = async () => {
    setLoading(true);
    setDownloadError(null);
    try {
      const response = await api.get(templateEndpoint || `/bulk/template/${entity}`, {
        responseType: 'blob',
      });
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entity}_template.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setUploadError(null);
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(uploadEndpoint || `/bulk/upload/${entity}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess(true);
      e.target.value = '';
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === 'object' && detail.errors) {
        setUploadError(detail.errors.map(er => `Fila ${er.row} [${er.field}]: ${er.message}`).join(' | '));
      } else {
        setUploadError(detail || err.message || 'Upload failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-xl font-semibold text-white">Carga Masiva de {entity}</h3>
        <p className="text-gray-400 text-sm">
          Carga muchos datos a la vez desde una planilla de Excel. Descargá el Template, llenalo con tus datos y Subilo.
        </p>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleDownload}
          disabled={loading}
          className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm font-semibold"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Descargando...
            </>
          ) : (
            <>
              <Download size={20} />
              Descargar Template
            </>
          )}
        </button>

        <label
          htmlFor={`bulk-upload-input-${entity}`}
          className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Subiendo...
            </>
          ) : (
            <>
              <Upload size={20} />
              Subir Archivo
            </>
          )}
        </label>
        <input
          id={`bulk-upload-input-${entity}`}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {downloadError && (
        <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
          {downloadError}
        </div>
      )}

      {uploadError && (
        <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
          {uploadError}
        </div>
      )}

      {success && (
        <div className="bg-green-500/15 border border-green-500/30 rounded-lg px-4 py-3 text-green-400 text-sm flex items-center gap-2">
          <CheckCircle size={20} />
          <span>Archivo subido correctamente</span>
        </div>
      )}
    </div>
  );
};

export default BulkUpload;