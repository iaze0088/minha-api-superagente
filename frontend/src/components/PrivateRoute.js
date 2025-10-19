import { Navigate } from 'react-router-dom';
import { getAuth } from '../lib/auth';

const PrivateRoute = ({ children, requiredType }) => {
  const { token, userType } = getAuth();

  if (!token) {
    return <Navigate to="/" />;
  }

  if (requiredType && userType !== requiredType) {
    return <Navigate to="/" />;
  }

  return children;
};

export default PrivateRoute;
