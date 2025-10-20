export const setAuth = (token, userType, userData) => {
  localStorage.setItem('token', token);
  localStorage.setItem('user_type', userType);
  localStorage.setItem('user_data', JSON.stringify(userData));
};

export const getAuth = () => {
  const token = localStorage.getItem('token');
  const userType = localStorage.getItem('user_type');
  let userData = {};
  try {
    const storedData = localStorage.getItem('user_data');
    userData = storedData ? JSON.parse(storedData) : {};
  } catch (e) {
    console.warn('Error parsing user_data from localStorage:', e);
    userData = {};
  }
  return { token, userType, userData };
};

export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user_type');
  localStorage.removeItem('user_data');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};
