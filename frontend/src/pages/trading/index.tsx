import styled from 'styled-components';
import BrokerStatusPanel from '../../components/trading/BrokerStatusPanel';
import ExecutionConsole from '../../components/trading/ExecutionConsole';
import StrategyCatalog from '../../components/trading/StrategyCatalog';
import TradingChart from '../../components/trading/TradingChart';
import TargetBridgePanel from '../../components/trading/TargetBridgePanel';

const Page = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0a0f1a;
  color: #e5e7eb;
  font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
  overflow: hidden;
`;

const TopBar = styled.div`
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #111827;
  border-bottom: 1px solid #1f2937;
  gap: 16px;
  flex-shrink: 0;
`;

const Logo = styled.span`
  font-size: 16px;
  font-weight: 800;
  color: #60a5fa;
  letter-spacing: 0.05em;
`;

const NavLink = styled.a`
  font-size: 13px;
  color: #6b7280;
  text-decoration: none;
  &:hover { color: #e5e7eb; }
`;

const ActiveLink = styled(NavLink)`
  color: #e5e7eb;
  border-bottom: 2px solid #60a5fa;
  padding-bottom: 2px;
`;

const Banner = styled.div`
  padding: 8px 20px;
  background: #1e293b;
  color: #fde68a;
  font-size: 12px;
  border-bottom: 1px solid #334155;
`;

const BrokerBar = styled.div`
  padding: 12px 20px;
  border-bottom: 1px solid #1f2937;
  flex-shrink: 0;
`;

const MainGrid = styled.div`
  display: grid;
  grid-template-columns: 300px 1fr 340px;
  gap: 12px;
  padding: 12px 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
`;

const Col = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
`;

export default function TradingPage() {
  return (
    <Page>
      <TopBar>
        <Logo>TSD</Logo>
        <NavLink href="/">Workflow</NavLink>
        <ActiveLink href="/trading">Trading</ActiveLink>
      </TopBar>

      <Banner>
        Prototype workbench — charts may still use fixtures. Paper target bridge is authoritative for
        demo fills. Live trading disabled. Server mode/token gates apply.
      </Banner>

      <BrokerBar>
        <BrokerStatusPanel />
      </BrokerBar>

      <MainGrid>
        <Col>
          <StrategyCatalog />
          <TargetBridgePanel />
        </Col>
        <Col>
          <TradingChart />
        </Col>
        <Col>
          <ExecutionConsole />
        </Col>
      </MainGrid>
    </Page>
  );
}
