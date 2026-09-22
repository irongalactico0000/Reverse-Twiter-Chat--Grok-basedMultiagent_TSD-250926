import { Route, Routes } from 'react-router';
import HomePage from './pages/home';
import TradingPage from './pages/trading';

const Router = () => {
  return (
    <Routes>
      <Route path={'/'} element={<HomePage />} />
      <Route path={'/trading'} element={<TradingPage />} />
    </Routes>
  );
};

export default Router;
