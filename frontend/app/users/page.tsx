'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { usersAPI } from '@/lib/api/users';
import { User, UserCreate, UserUpdate } from '@/lib/types';
import { parseError } from '@/lib/utils/error';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Loading } from '@/components/ui/Loading';
import { Card } from '@/components/ui/Card';
import { Search, Plus, Edit, Trash2, User as UserIcon, Phone, Mail, Calendar, Lock } from 'lucide-react';
import { validatePhone, validateEmail, formatPhoneInput } from '@/lib/utils/validation';

export default function UsersPage() {
  const { isAdmin } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form state
  const [formData, setFormData] = useState<UserCreate>({
    username: '',
    password: '',
    full_name: '',
    phone: '',
    date_of_birth: '',
    email: '',
    role: 'employee',
  });

  const [editData, setEditData] = useState<UserUpdate>({
    full_name: '',
    phone: '',
    date_of_birth: '',
    email: '',
    password: '',
  });

  // Load users
  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await usersAPI.listUsers(search);
      setUsers(data);
    } catch (err: any) {
      setError(parseError(err) || 'Không thể tải danh sách người dùng');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      const timer = setTimeout(() => {
        loadUsers();
      }, 300); // Debounce search

      return () => clearTimeout(timer);
    }
  }, [isAdmin, search]);

  // Create user
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      // Validate email format (phone is already formatted by formatPhoneInput)
      if (formData.email && formData.email.trim() && !validateEmail(formData.email.trim())) {
        setError('Email không đúng định dạng. Vui lòng nhập email hợp lệ.');
        return;
      }

      // Prepare user data - only include non-empty fields
      const userData: any = {
        username: formData.username.trim(),
        password: formData.password,
        role: formData.role || 'employee',
      };
      
      // Add optional fields only if they have values
      if (formData.full_name && formData.full_name.trim()) {
        userData.full_name = formData.full_name.trim();
      }
      
      if (formData.phone && formData.phone.trim()) {
        userData.phone = formData.phone.trim();
      }
      
      // Format date_of_birth: send ISO string with time if provided
      // Pydantic accepts ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SSZ
      if (formData.date_of_birth && formData.date_of_birth.trim()) {
        // Format: YYYY-MM-DD -> YYYY-MM-DDT00:00:00Z (ISO 8601 with UTC timezone)
        // Note: Pydantic can parse both with and without timezone
        userData.date_of_birth = `${formData.date_of_birth}T00:00:00`;
      }
      
      // Email: only send if valid email (not empty string)
      if (formData.email && formData.email.trim()) {
        userData.email = formData.email.trim();
      }
      
      console.log('Creating user with data:', userData);
      
      const createdUser = await usersAPI.createUser(userData);
      setSuccess('Tạo người dùng thành công');
      setError(''); // Clear any previous errors
      
      // Update users list with new user (including password)
      setUsers(prev => [createdUser, ...prev]);
      
      // Close create modal and reset form
      setShowCreateModal(false);
      setFormData({
        username: '',
        password: '',
        full_name: '',
        phone: '',
        date_of_birth: '',
        email: '',
        role: 'employee',
      });
      setSuccess('');
    } catch (err: any) {
      console.error('Error creating user:', err);
      const errorMessage = parseError(err) || 'Không thể tạo người dùng. Vui lòng kiểm tra lại thông tin hoặc thử lại sau.';
      setError(errorMessage);
    }
  };

  // Update user
  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    setError('');
    setSuccess('');

    try {
      // Validate email format (phone is already formatted by formatPhoneInput)
      if (editData.email && editData.email.trim() && !validateEmail(editData.email.trim())) {
        setError('Email không đúng định dạng. Vui lòng nhập email hợp lệ.');
        return;
      }

      // Prepare update data - only include fields that have values
      const updateData: any = {};
      
      if (editData.full_name && editData.full_name.trim()) {
        updateData.full_name = editData.full_name.trim();
      }
      
      if (editData.phone && editData.phone.trim()) {
        updateData.phone = editData.phone.trim();
      }
      
      // Format date_of_birth: send ISO string with time if provided
      if (editData.date_of_birth && editData.date_of_birth.trim()) {
        updateData.date_of_birth = `${editData.date_of_birth}T00:00:00`;
      }
      
      // Email: only send if valid email (not empty string)
      if (editData.email !== undefined) {
        if (editData.email && editData.email.trim()) {
          updateData.email = editData.email.trim();
        } else {
          // Send null to clear email
          updateData.email = null;
        }
      }

      // Password: only send if provided (not empty)
      const newPassword = editData.password && editData.password.trim() ? editData.password.trim() : null;
      if (newPassword) {
        if (newPassword.length < 6) {
          setError('Mật khẩu phải có ít nhất 6 ký tự.');
          return;
        }
        updateData.password = newPassword;
      }
      
      console.log('Updating user with data:', updateData);
      
      const updatedUser = await usersAPI.updateUser(selectedUser.id, updateData);
      setSuccess('Cập nhật người dùng thành công');
      setError(''); // Clear any previous errors
      
      // Update users list with updated user (including password if updated)
      setUsers(prev => prev.map(u => u.id === updatedUser.id ? updatedUser : u));
      
      // Close modal after a short delay to show success message
      setTimeout(() => {
        setShowEditModal(false);
        setSelectedUser(null);
        setEditData({
          full_name: '',
          phone: '',
          date_of_birth: '',
          email: '',
          password: '',
        });
        setSuccess('');
      }, 1000);
    } catch (err: any) {
      console.error('Error updating user:', err);
      const errorMessage = parseError(err) || 'Không thể cập nhật người dùng. Vui lòng kiểm tra lại thông tin.';
      setError(errorMessage);
    }
  };

  // Delete user
  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    setError('');
    setSuccess('');

    try {
      await usersAPI.deleteUser(selectedUser.id);
      setSuccess('Xóa người dùng thành công');
      setError(''); // Clear any previous errors
      
      // Close modal after a short delay to show success message
      setTimeout(() => {
        setShowDeleteModal(false);
        setSelectedUser(null);
        setSuccess('');
      }, 1000);
      loadUsers();
    } catch (err: any) {
      const errorMessage = parseError(err) || 'Không thể xóa người dùng. Vui lòng thử lại.';
      setError(errorMessage);
    }
  };

  // Open edit modal
  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setEditData({
      full_name: user.full_name || '',
      phone: user.phone || '',
      date_of_birth: user.date_of_birth ? user.date_of_birth.split('T')[0] : '',
      email: user.email || '',
      password: '', // Password field is always empty (cannot view existing password)
    });
    setShowEditModal(true);
  };

  // Open delete modal
  const openDeleteModal = (user: User) => {
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  if (!isAdmin) {
    return (
      <ProtectedRoute requireAdmin>
        <div>Không có quyền truy cập</div>
      </ProtectedRoute>
    );
  }

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
                  <h1 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h1>
                  <p className="mt-1 text-sm text-gray-600">
                    Quản lý tài khoản người dùng và nhân viên
                  </p>
                </div>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  variant="primary"
                  size="md"
                  className="flex items-center space-x-2"
                >
                  <Plus className="h-4 w-4" />
                  <span>Tạo người dùng</span>
                </Button>
              </div>

              {/* Search */}
              <div className="mb-6">
                <Input
                  type="text"
                  placeholder="Tìm kiếm theo tên đăng nhập, tên, số điện thoại, email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  icon={<Search className="h-5 w-5" />}
                />
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

              {/* Users Table */}
              {loading ? (
                <div className="py-12">
                  <Loading size="lg" text="Đang tải danh sách người dùng..." />
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-12">
                  <UserIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Không có người dùng nào</p>
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
                          Tên đăng nhập
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Họ tên
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Số điện thoại
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Ngày sinh
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Vai trò
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Thao tác
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr
                          key={user.id}
                          className="hover:bg-gray-50 transition-colors duration-150 cursor-pointer"
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {user.id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <UserIcon className="h-4 w-4 text-gray-400" />
                              <span>{user.username}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.full_name || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <Phone className="h-4 w-4 text-gray-400" />
                              <span>{user.phone || '-'}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <Calendar className="h-4 w-4 text-gray-400" />
                              <span>
                                {user.date_of_birth 
                                  ? new Date(user.date_of_birth).toLocaleDateString('vi-VN', {
                                      year: 'numeric',
                                      month: '2-digit',
                                      day: '2-digit'
                                    })
                                  : '-'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <Mail className="h-4 w-4 text-gray-400" />
                              <span>{user.email || '-'}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <Badge variant={user.role === 'admin' ? 'admin' : 'employee'}>
                              {user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openEditModal(user)}
                                className="flex items-center space-x-1"
                              >
                                <Edit className="h-4 w-4" />
                                <span>Sửa</span>
                              </Button>
                              {user.role !== 'admin' && (
                                <Button
                                  variant="danger"
                                  size="sm"
                                  onClick={() => openDeleteModal(user)}
                                  className="flex items-center space-x-1"
                                >
                                  <Trash2 className="h-4 w-4" />
                                  <span>Xóa</span>
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {/* Create User Modal */}
            <Modal
              isOpen={showCreateModal}
              onClose={() => {
                setShowCreateModal(false);
                setError('');
                setSuccess('');
                setFormData({
                  username: '',
                  password: '',
                  full_name: '',
                  phone: '',
                  date_of_birth: '',
                  email: '',
                  role: 'employee',
                });
              }}
              title="Tạo người dùng mới"
              size="md"
            >
              <form onSubmit={handleCreateUser} className="space-y-4">
                {/* Error Alert */}
                {error && (
                  <Alert
                    type="error"
                    message={error}
                    onClose={() => setError('')}
                  />
                )}

                {/* Success Alert */}
                {success && (
                  <Alert
                    type="success"
                    message={success}
                    onClose={() => setSuccess('')}
                  />
                )}

                <Input
                  label="Tên đăng nhập"
                  type="text"
                  placeholder="Nhập tên đăng nhập"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  icon={<UserIcon className="h-5 w-5" />}
                  required
                />

                <Input
                  label="Mật khẩu"
                  type="password"
                  placeholder="Nhập mật khẩu"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  icon={<Lock className="h-5 w-5" />}
                  required
                />

                <Input
                  label="Họ tên"
                  type="text"
                  placeholder="Nhập họ tên"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  icon={<UserIcon className="h-5 w-5" />}
                />

                <Input
                  label="Số điện thoại"
                  type="text"
                  placeholder="Nhập số điện thoại (chỉ số)"
                  value={formData.phone}
                  onChange={(e) => {
                    const formatted = formatPhoneInput(e.target.value);
                    setFormData({ ...formData, phone: formatted });
                  }}
                  icon={<Phone className="h-5 w-5" />}
                />

                <Input
                  label="Ngày sinh"
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  icon={<Calendar className="h-5 w-5" />}
                />

                <Input
                  label="Email (tùy chọn)"
                  type="email"
                  placeholder="Nhập email (ví dụ: user@example.com)"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  icon={<Mail className="h-5 w-5" />}
                  error={formData.email && formData.email.trim() && !validateEmail(formData.email.trim()) ? 'Email không đúng định dạng' : undefined}
                />

                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setShowCreateModal(false);
                      setError('');
                      setSuccess('');
                      setFormData({
                        username: '',
                        password: '',
                        full_name: '',
                        phone: '',
                        date_of_birth: '',
                        email: '',
                        role: 'employee',
                      });
                    }}
                  >
                    Hủy
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                  >
                    Tạo
                  </Button>
                </div>
              </form>
            </Modal>

            {/* Edit User Modal */}
            {showEditModal && selectedUser && (
              <Modal
                isOpen={showEditModal}
                onClose={() => {
                  setShowEditModal(false);
                  setError('');
                  setSuccess('');
                  setSelectedUser(null);
                  setEditData({
                    full_name: '',
                    phone: '',
                    date_of_birth: '',
                    email: '',
                    password: '',
                  });
                }}
                title="Sửa người dùng"
                size="md"
              >
                <form onSubmit={handleUpdateUser} className="space-y-4">
                  {/* Error Alert */}
                  {error && (
                    <Alert
                      type="error"
                      message={error}
                      onClose={() => setError('')}
                    />
                  )}

                  {/* Success Alert */}
                  {success && (
                    <Alert
                      type="success"
                      message={success}
                      onClose={() => setSuccess('')}
                    />
                  )}

                  <Input
                    label="Họ tên"
                    type="text"
                    placeholder="Nhập họ tên"
                    value={editData.full_name}
                    onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                    icon={<UserIcon className="h-5 w-5" />}
                  />

                  <Input
                    label="Số điện thoại"
                    type="text"
                    placeholder="Nhập số điện thoại (chỉ số)"
                    value={editData.phone}
                    onChange={(e) => {
                      const formatted = formatPhoneInput(e.target.value);
                      setEditData({ ...editData, phone: formatted });
                    }}
                    icon={<Phone className="h-5 w-5" />}
                  />

                  <Input
                    label="Ngày sinh"
                    type="date"
                    value={editData.date_of_birth}
                    onChange={(e) => setEditData({ ...editData, date_of_birth: e.target.value })}
                    icon={<Calendar className="h-5 w-5" />}
                  />

                  <Input
                    label="Email"
                    type="email"
                    placeholder="Nhập email (ví dụ: user@example.com)"
                    value={editData.email}
                    onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                    icon={<Mail className="h-5 w-5" />}
                    error={editData.email && editData.email.trim() && !validateEmail(editData.email.trim()) ? 'Email không đúng định dạng' : undefined}
                  />

                  <div className="border-t border-gray-200 pt-4">
                    <Input
                      label="Mật khẩu mới"
                      type="password"
                      placeholder="Nhập mật khẩu mới (để trống nếu không muốn đổi)"
                      value={editData.password || ''}
                      onChange={(e) => setEditData({ ...editData, password: e.target.value })}
                      icon={<Lock className="h-5 w-5" />}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Để trống nếu không muốn thay đổi mật khẩu. Mật khẩu phải có ít nhất 6 ký tự.
                    </p>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        setShowEditModal(false);
                        setError('');
                        setSuccess('');
                        setSelectedUser(null);
                        setEditData({
                          full_name: '',
                          phone: '',
                          date_of_birth: '',
                          email: '',
                          password: '',
                        });
                      }}
                    >
                      Hủy
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                    >
                      Cập nhật
                    </Button>
                  </div>
                </form>
              </Modal>
            )}

            {/* Delete User Modal */}
            {showDeleteModal && selectedUser && (
              <Modal
                isOpen={showDeleteModal}
                onClose={() => {
                  setShowDeleteModal(false);
                  setError('');
                  setSuccess('');
                  setSelectedUser(null);
                }}
                title="Xác nhận xóa"
                size="sm"
              >
                <div className="space-y-4">
                  {/* Error Alert */}
                  {error && (
                    <Alert
                      type="error"
                      message={error}
                      onClose={() => setError('')}
                    />
                  )}

                  {/* Success Alert */}
                  {success && (
                    <Alert
                      type="success"
                      message={success}
                      onClose={() => setSuccess('')}
                    />
                  )}

                  <p className="text-sm text-gray-600">
                    Bạn có chắc chắn muốn xóa người dùng <strong className="text-gray-900">{selectedUser.username}</strong>?
                  </p>
                  <p className="text-xs text-gray-500">
                    Hành động này không thể hoàn tác.
                  </p>
                  <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => {
                          setShowDeleteModal(false);
                          setError('');
                          setSuccess('');
                          setSelectedUser(null);
                        }}
                      >
                        Hủy
                      </Button>
                    <Button
                      type="button"
                      variant="danger"
                      onClick={handleDeleteUser}
                    >
                      Xóa
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

