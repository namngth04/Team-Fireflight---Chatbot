/**
 * Parse error response from API and return a user-friendly error message
 */
export function parseError(error: any): string {
  if (!error) {
    return 'Đã xảy ra lỗi không xác định. Vui lòng thử lại sau.';
  }

  // Log error for debugging
  console.error('Error details:', error);

  // Network error (no response from server)
  if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
    return 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet và thử lại.';
  }

  // Timeout error
  if (error.code === 'ETIMEDOUT' || error.message?.includes('timeout')) {
    return 'Request timeout. Vui lòng thử lại sau.';
  }

  // If error.response exists (axios error)
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    // Log response data for debugging
    console.error('Error response data:', data);
    
    // Handle different HTTP status codes
    if (status === 401) {
      return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    }
    if (status === 403) {
      return 'Bạn không có quyền thực hiện hành động này.';
    }
    if (status === 404) {
      return 'Không tìm thấy tài nguyên. Vui lòng kiểm tra lại.';
    }
    if (status === 422) {
      // Validation error - parse detail
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail)) {
        const errors = data.detail
          .map((err: any) => {
            if (typeof err === 'string') {
              return err;
            }
            if (err.msg) {
              // Format location: body.field_name -> "field_name"
              const loc = err.loc 
                ? err.loc.filter((l: string) => l !== 'body' && l !== 'query' && l !== 'path').join('.')
                : '';
              return loc ? `${loc}: ${err.msg}` : err.msg;
            }
            return JSON.stringify(err);
          })
          .join(', ');
        return errors;
      }
      if (typeof data.detail === 'object' && data.detail !== null) {
        if (data.detail.msg) {
          const loc = data.detail.loc 
            ? data.detail.loc.filter((l: string) => l !== 'body' && l !== 'query' && l !== 'path').join('.')
            : '';
          return loc ? `${loc}: ${data.detail.msg}` : data.detail.msg;
        }
        return 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại thông tin.';
      }
      return 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại thông tin.';
    }
    if (status === 500) {
      return 'Lỗi server. Vui lòng thử lại sau hoặc liên hệ quản trị viên.';
    }
    if (status >= 500) {
      return 'Lỗi server. Vui lòng thử lại sau.';
    }
    if (status >= 400) {
      return 'Lỗi yêu cầu. Vui lòng kiểm tra lại thông tin.';
    }
    
    // If detail is a string, return it directly
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    
    // If detail is an array (validation errors from Pydantic)
    if (Array.isArray(data.detail)) {
      const errors = data.detail
        .map((err: any) => {
          if (typeof err === 'string') {
            return err;
          }
          if (err.msg) {
            // Format location: body.field_name -> "field_name"
            const loc = err.loc 
              ? err.loc.filter((l: string) => l !== 'body' && l !== 'query' && l !== 'path').join('.')
              : '';
            return loc ? `${loc}: ${err.msg}` : err.msg;
          }
          return JSON.stringify(err);
        })
        .join(', ');
      
      console.error('Parsed validation errors:', errors);
      return errors;
    }
    
    // If detail is an object
    if (typeof data.detail === 'object' && data.detail !== null) {
      if (data.detail.msg) {
        const loc = data.detail.loc 
          ? data.detail.loc.filter((l: string) => l !== 'body' && l !== 'query' && l !== 'path').join('.')
          : '';
        return loc ? `${loc}: ${data.detail.msg}` : data.detail.msg;
      }
      return JSON.stringify(data.detail);
    }
    
    // If data itself is a string
    if (typeof data === 'string') {
      return data;
    }
  }
  
  // If error.message exists
  if (error.message) {
    // Check for common error messages
    if (error.message.includes('Network Error')) {
      return 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet và thử lại.';
    }
    if (error.message.includes('timeout')) {
      return 'Request timeout. Vui lòng thử lại sau.';
    }
    return error.message;
  }
  
  // Fallback to JSON string
  return 'Đã xảy ra lỗi không xác định. Vui lòng thử lại sau.';
}

