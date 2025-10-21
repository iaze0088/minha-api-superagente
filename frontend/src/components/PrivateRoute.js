import { Navigate } from 'react-router-dom';
import { getAuth } from '../lib/auth';

const PrivateRoute = ({ children, requiredType }) => {
  const { token, userType } = getAuth();
  
  console.log('PrivateRoute check:', { token: !!token, userType, requiredType });

  if (!token) {
    console.log('No token, redirecting to /');
    return <Navigate to="/" />;
  }

  if (requiredType && userType !== requiredType) {
    console.log(`UserType mismatch: ${userType} !== ${requiredType}, redirecting to /`);
    return <Navigate to="/" />;
  }

  console.log('PrivateRoute passed, rendering children');
  return children;
};

export default PrivateRoute;
