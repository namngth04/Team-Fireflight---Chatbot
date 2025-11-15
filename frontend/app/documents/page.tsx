'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { documentsAPI } from '@/lib/api/documents';
import { Document, DocumentType, DocumentUpdate } from '@/lib/types';
import { parseError } from '@/lib/utils/error';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { Loading } from '@/components/ui/Loading';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { FileUpload } from '@/components/ui/FileUpload';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  FileText,
  Upload as UploadIcon,
  Calendar,
  User,
  Eye,
  Filter,
} from 'lucide-react';

// Document type options with Vietnamese labels
const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: 'policy', label: 'Chính sách / HR' },
  { value: 'ops', label: 'Vận hành / Kỹ thuật' },
];

const getDocumentTypeLabel = (type: DocumentType): string => {
  return DOCUMENT_TYPE_OPTIONS.find(opt => opt.value === type)?.label || type;
};

export default function DocumentsPage() {
  const { isAdmin } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [documentTypeFilter, setDocumentTypeFilter] = useState<string>('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocumentType, setUploadDocumentType] = useState<DocumentType>('policy');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  // Edit form state
  const [editData, setEditData] = useState<DocumentUpdate>({
    description: '',
    document_type: 'policy',
  });

  // Load documents
  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await documentsAPI.listDocuments(
        documentTypeFilter || undefined,
        search || undefined
      );
      setDocuments(data);
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể tải danh sách tài liệu. Vui lòng thử lại.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      const timer = setTimeout(() => {
        loadDocuments();
      }, 300); // Debounce search

      return () => clearTimeout(timer);
    }
  }, [isAdmin, search, documentTypeFilter]);

  // Upload document
  const handleUpload = async () => {
    if (!uploadFile) {
      setError('Vui lòng chọn file để upload');
      return;
    }

    setError('');
    setSuccess('');
    setUploading(true);

    try {
      await documentsAPI.uploadDocument(
        uploadFile,
        uploadDocumentType,
        uploadDescription || undefined
      );
      setSuccess('Upload tài liệu thành công');
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadDocumentType('policy');
      setUploadDescription('');
      setTimeout(() => {
        setSuccess('');
      }, 1000);
      loadDocuments();
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể upload tài liệu. Vui lòng thử lại.';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  // Update document
  const handleUpdate = async () => {
    if (!selectedDocument) return;

    setError('');
    setSuccess('');

    try {
      await documentsAPI.updateDocument(selectedDocument.id, editData);
      setSuccess('Cập nhật tài liệu thành công');
      setShowEditModal(false);
      setSelectedDocument(null);
      setTimeout(() => {
        setSuccess('');
      }, 1000);
      loadDocuments();
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể cập nhật tài liệu. Vui lòng thử lại.';
      setError(errorMessage);
    }
  };

  // Delete document
  const handleDelete = async () => {
    if (!selectedDocument) return;

    setError('');
    setSuccess('');

    try {
      await documentsAPI.deleteDocument(selectedDocument.id);
      setSuccess('Xóa tài liệu thành công');
      setShowDeleteModal(false);
      setSelectedDocument(null);
      setTimeout(() => {
        setSuccess('');
      }, 1000);
      loadDocuments();
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể xóa tài liệu. Vui lòng thử lại.';
      setError(errorMessage);
    }
  };

  // Open edit modal
  const openEditModal = (document: Document) => {
    setSelectedDocument(document);
    setEditData({
      description: document.description || '',
      document_type: document.document_type,
    });
    setShowEditModal(true);
  };

  // Open delete modal
  const openDeleteModal = (document: Document) => {
    setSelectedDocument(document);
    setShowDeleteModal(true);
  };

  // Open view modal
  const openViewModal = (document: Document) => {
    setSelectedDocument(document);
    setShowViewModal(true);
  };

  return (
    <ProtectedRoute requireAdmin>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <Card>
              {/* Header */}
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Quản lý tài liệu</h1>
                  <p className="mt-1 text-sm text-gray-600">
                    Upload và quản lý tài liệu cho chatbot
                  </p>
                </div>
                <Button
                  onClick={() => setShowUploadModal(true)}
                  variant="primary"
                  size="md"
                  className="flex items-center space-x-2"
                >
                  <UploadIcon className="h-4 w-4" />
                  <span>Upload tài liệu</span>
                </Button>
              </div>

              {/* Filters */}
              <div className="mb-6 flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    type="text"
                    placeholder="Tìm kiếm theo tên file, mô tả..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    icon={<Search className="h-5 w-5" />}
                  />
                </div>
                <div className="sm:w-64">
                  <div className="relative">
                    <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <select
                      value={documentTypeFilter}
                      onChange={(e) => setDocumentTypeFilter(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
                    >
                      <option value="">Tất cả loại</option>
                      {DOCUMENT_TYPE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Messages */}
              {error && (
                <div className="mb-4">
                  <Alert
                    type="error"
                    message={error}
                    onClose={() => setError('')}
                  />
                </div>
              )}
              {success && (
                <div className="mb-4">
                  <Alert
                    type="success"
                    message={success}
                    onClose={() => setSuccess('')}
                  />
                </div>
              )}

              {/* Documents Table */}
              {loading ? (
                <div className="py-12">
                  <Loading size="lg" text="Đang tải danh sách tài liệu..." />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Không có tài liệu nào</p>
                  {search && (
                    <p className="text-sm text-gray-500 mt-2">
                      Không tìm thấy kết quả cho "{search}"
                    </p>
                  )}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Tên file
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Loại
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Mô tả
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Ngày upload
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Người upload
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Thao tác
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {documents.map((document) => (
                        <tr
                          key={document.id}
                          className="hover:bg-gray-50 transition-colors duration-150"
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {document.id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <FileText className="h-4 w-4 text-gray-400" />
                              <span>{document.filename}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <Badge variant="employee">
                              {getDocumentTypeLabel(document.document_type)}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900">
                            <div className="max-w-xs truncate">
                              {document.description || '-'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <Calendar className="h-4 w-4 text-gray-400" />
                              <span>
                                {new Date(document.uploaded_at).toLocaleDateString('vi-VN', {
                                  year: 'numeric',
                                  month: '2-digit',
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <User className="h-4 w-4 text-gray-400" />
                              <span>ID: {document.uploaded_by}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openViewModal(document)}
                                className="flex items-center space-x-1"
                              >
                                <Eye className="h-4 w-4" />
                                <span>Xem</span>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openEditModal(document)}
                                className="flex items-center space-x-1"
                              >
                                <Edit className="h-4 w-4" />
                                <span>Sửa</span>
                              </Button>
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => openDeleteModal(document)}
                                className="flex items-center space-x-1"
                              >
                                <Trash2 className="h-4 w-4" />
                                <span>Xóa</span>
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {/* Upload Modal */}
            <Modal
              isOpen={showUploadModal}
              onClose={() => {
                setShowUploadModal(false);
                setError('');
                setSuccess('');
                setUploadFile(null);
                setUploadDocumentType('policy');
                setUploadDescription('');
              }}
              title="Upload tài liệu"
              size="lg"
            >
              <div className="space-y-4">
                {/* Error/Success Alerts */}
                {error && (
                  <Alert
                    type="error"
                    message={error}
                    onClose={() => setError('')}
                  />
                )}
                {success && (
                  <Alert
                    type="success"
                    message={success}
                    onClose={() => setSuccess('')}
                  />
                )}

                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chọn file
                  </label>
                  <FileUpload
                    onFileSelect={(file) => setUploadFile(file)}
                    accept=".txt"
                    maxSize={50 * 1024 * 1024}
                  />
                </div>

                {/* Document Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Loại tài liệu
                  </label>
                  <select
                    value={uploadDocumentType}
                    onChange={(e) => setUploadDocumentType(e.target.value as DocumentType)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
                  >
                    {DOCUMENT_TYPE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Mô tả (tùy chọn)
                  </label>
                  <textarea
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    placeholder="Nhập mô tả cho tài liệu..."
                    rows={3}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 placeholder:text-gray-500"
                  />
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setShowUploadModal(false);
                      setError('');
                      setSuccess('');
                      setUploadFile(null);
                      setUploadDocumentType('policy');
                      setUploadDescription('');
                    }}
                  >
                    Hủy
                  </Button>
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleUpload}
                    isLoading={uploading}
                    disabled={!uploadFile || uploading}
                  >
                    Upload
                  </Button>
                </div>
              </div>
            </Modal>

            {/* Edit Modal */}
            {showEditModal && selectedDocument && (
              <Modal
                isOpen={showEditModal}
                onClose={() => {
                  setShowEditModal(false);
                  setError('');
                  setSuccess('');
                  setSelectedDocument(null);
                }}
                title="Sửa tài liệu"
                size="md"
              >
                <div className="space-y-4">
                  {/* Error/Success Alerts */}
                  {error && (
                    <Alert
                      type="error"
                      message={error}
                      onClose={() => setError('')}
                    />
                  )}
                  {success && (
                    <Alert
                      type="success"
                      message={success}
                      onClose={() => setSuccess('')}
                    />
                  )}

                  {/* Document Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Loại tài liệu
                    </label>
                    <select
                      value={editData.document_type}
                      onChange={(e) => setEditData({ ...editData, document_type: e.target.value as DocumentType })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      {DOCUMENT_TYPE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Mô tả
                    </label>
                    <textarea
                      value={editData.description || ''}
                      onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                      placeholder="Nhập mô tả cho tài liệu..."
                      rows={3}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  {/* Actions */}
                  <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        setShowEditModal(false);
                        setError('');
                        setSuccess('');
                        setSelectedDocument(null);
                      }}
                    >
                      Hủy
                    </Button>
                    <Button
                      type="button"
                      variant="primary"
                      onClick={handleUpdate}
                    >
                      Cập nhật
                    </Button>
                  </div>
                </div>
              </Modal>
            )}

            {/* Delete Modal */}
            {showDeleteModal && selectedDocument && (
              <Modal
                isOpen={showDeleteModal}
                onClose={() => {
                  setShowDeleteModal(false);
                  setError('');
                  setSuccess('');
                  setSelectedDocument(null);
                }}
                title="Xác nhận xóa"
                size="sm"
              >
                <div className="space-y-4">
                  {/* Error/Success Alerts */}
                  {error && (
                    <Alert
                      type="error"
                      message={error}
                      onClose={() => setError('')}
                    />
                  )}
                  {success && (
                    <Alert
                      type="success"
                      message={success}
                      onClose={() => setSuccess('')}
                    />
                  )}

                  <p className="text-sm text-gray-600">
                    Bạn có chắc chắn muốn xóa tài liệu <strong className="text-gray-900">{selectedDocument.filename}</strong>?
                  </p>
                  <p className="text-xs text-gray-500">
                    Hành động này không thể hoàn tác. Tài liệu sẽ bị xóa khỏi database và storage.
                  </p>
                  <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        setShowDeleteModal(false);
                        setError('');
                        setSuccess('');
                        setSelectedDocument(null);
                      }}
                    >
                      Hủy
                    </Button>
                    <Button
                      type="button"
                      variant="danger"
                      onClick={handleDelete}
                    >
                      Xóa
                    </Button>
                  </div>
                </div>
              </Modal>
            )}

            {/* View Modal */}
            {showViewModal && selectedDocument && (
              <Modal
                isOpen={showViewModal}
                onClose={() => {
                  setShowViewModal(false);
                  setSelectedDocument(null);
                }}
                title="Chi tiết tài liệu"
                size="lg"
              >
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tên file
                    </label>
                    <p className="text-sm text-gray-900">{selectedDocument.filename}</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Loại tài liệu
                    </label>
                    <Badge variant="employee">
                      {getDocumentTypeLabel(selectedDocument.document_type)}
                    </Badge>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mô tả
                    </label>
                    <p className="text-sm text-gray-900">
                      {selectedDocument.description || '-'}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ngày upload
                    </label>
                    <p className="text-sm text-gray-900">
                      {new Date(selectedDocument.uploaded_at).toLocaleString('vi-VN', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Người upload
                    </label>
                    <p className="text-sm text-gray-900">ID: {selectedDocument.uploaded_by}</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      File path
                    </label>
                    <p className="text-sm text-gray-500 font-mono break-all">
                      {selectedDocument.file_path}
                    </p>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        setShowViewModal(false);
                        setSelectedDocument(null);
                      }}
                    >
                      Đóng
                    </Button>
                  </div>
                </div>
              </Modal>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

