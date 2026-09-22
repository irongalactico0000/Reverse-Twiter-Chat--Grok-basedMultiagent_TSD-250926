import { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';

const Wrapper = styled.div`
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
`;

const SymbolInput = styled.input`
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 4px;
  color: #f3f4f6;
  padding: 5px 10px;
  font-size: 14px;
  font-weight: 700;
  width: 100px;
  text-transform: uppercase;
  &:focus { outline: none; border-color: #60a5fa; }
`;

const PriceBig = styled.span`
  color: #f3f4f6;
  font-size: 22px;
  font-weight: 700;
`;

const PriceChange = styled.span<{ positive?: boolean }>`
  font-size: 13px;
  font-weight: 600;
  color: ${p => p.positive ? '#86efac' : '#fca5a5'};
`;

const ChartContainer = styled.div`
  flex: 1;
  min-height: 0;
  border-radius: 4px;
  overflow: hidden;
  background: #0f172a;
`;

const OrderBookGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
`;

const BookPanel = styled.div`
  background: #0f172a;
  border: 1px solid #1f2937;
  border-radius: 6px;
  padding: 8px;
`;

const BookTitle = styled.div`
  font-size: 11px;
  color: #6b7280;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 6px;
`;

const BookRow = styled.div<{ side: 'bid' | 'ask'; intensity: number }>`
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  padding: 2px 0;
  position: relative;
  &::before {
    content: '';
    position: absolute;
    top: 0; bottom: 0;
    ${p => p.side === 'bid' ? 'right: 0;' : 'left: 0;'}
    width: ${p => p.intensity * 100}%;
    background: ${p => p.side === 'bid' ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)'};
    border-radius: 2px;
  }
`;

const BookPrice = styled.span<{ side: 'bid' | 'ask' }>`
  color: ${p => p.side === 'bid' ? '#86efac' : '#fca5a5'};
  font-weight: 600;
  z-index: 1;
  position: relative;
`;

const BookSize = styled.span`
  color: #6b7280;
  z-index: 1;
  position: relative;
`;

// Synthetic order book for demo purposes
function generateBook(midPrice: number, side: 'bid' | 'ask', levels = 6) {
  return Array.from({ length: levels }, (_, i) => ({
    price: side === 'bid' ? midPrice - (i + 1) * 0.05 : midPrice + (i + 1) * 0.05,
    size: Math.floor(Math.random() * 500 + 50),
  }));
}

export default function TradingChart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const [symbol, setSymbol] = useState('AAPL');
  const [inputSymbol, setInputSymbol] = useState('AAPL');
  const [price, setPrice] = useState(195.42);
  const [change, setChange] = useState(+1.23);
  const [bids, setBids] = useState(() => generateBook(195.42, 'bid'));
  const [asks, setAsks] = useState(() => generateBook(195.42, 'ask'));

  // Mount TradingView Lightweight Chart
  useEffect(() => {
    if (!chartRef.current) return;
    let chart: ReturnType<typeof import('lightweight-charts')['createChart']> | null = null;

    import('lightweight-charts').then(({ createChart, ColorType }) => {
      if (!chartRef.current) return;
      const container = chartRef.current;

      chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: '#0f172a' },
          textColor: '#6b7280',
        },
        grid: {
          vertLines: { color: '#1f2937' },
          horzLines: { color: '#1f2937' },
        },
        width: container.clientWidth,
        height: container.clientHeight,
        rightPriceScale: { borderColor: '#1f2937' },
        timeScale: { borderColor: '#1f2937', timeVisible: true },
      });

      const series = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
      });

      // Generate synthetic OHLC data for demo
      const now = Math.floor(Date.now() / 1000);
      const candles = Array.from({ length: 60 }, (_, i) => {
        const base = 195 + Math.sin(i / 10) * 3;
        const o = base + (Math.random() - 0.5) * 0.5;
        const c = base + (Math.random() - 0.5) * 0.5;
        const h = Math.max(o, c) + Math.random() * 0.3;
        const l = Math.min(o, c) - Math.random() * 0.3;
        return {
          time: (now - (60 - i) * 60) as unknown as import('lightweight-charts').Time,
          open: +o.toFixed(2),
          high: +h.toFixed(2),
          low: +l.toFixed(2),
          close: +c.toFixed(2),
        };
      });
      series.setData(candles);
      chart.timeScale().fitContent();

      const ro = new ResizeObserver(() => {
        if (chart && container) {
          chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
        }
      });
      ro.observe(container);

      return () => { ro.disconnect(); chart?.remove(); };
    });

    return () => { chart?.remove(); };
  }, [symbol]);

  // Tick order book
  useEffect(() => {
    const id = setInterval(() => {
      const mid = price + (Math.random() - 0.5) * 0.1;
      setPrice(+mid.toFixed(2));
      setChange(+(mid - 194.19).toFixed(2));
      setBids(generateBook(mid, 'bid'));
      setAsks(generateBook(mid, 'ask'));
    }, 2000);
    return () => clearInterval(id);
  }, [price]);

  const maxSize = Math.max(...bids.map(b => b.size), ...asks.map(a => a.size));

  return (
    <Wrapper>
      <Header>
        <SymbolInput
          value={inputSymbol}
          onChange={e => setInputSymbol(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && setSymbol(inputSymbol)}
        />
        <PriceBig>{price.toFixed(2)}</PriceBig>
        <PriceChange positive={change >= 0}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)} ({((change / 194.19) * 100).toFixed(2)}%)
        </PriceChange>
      </Header>

      <ChartContainer ref={chartRef} />

      <OrderBookGrid>
        <BookPanel>
          <BookTitle>Bids</BookTitle>
          {bids.map((b, i) => (
            <BookRow key={i} side="bid" intensity={b.size / maxSize}>
              <BookPrice side="bid">{b.price.toFixed(2)}</BookPrice>
              <BookSize>{b.size}</BookSize>
            </BookRow>
          ))}
        </BookPanel>
        <BookPanel>
          <BookTitle>Asks</BookTitle>
          {asks.map((a, i) => (
            <BookRow key={i} side="ask" intensity={a.size / maxSize}>
              <BookPrice side="ask">{a.price.toFixed(2)}</BookPrice>
              <BookSize>{a.size}</BookSize>
            </BookRow>
          ))}
        </BookPanel>
      </OrderBookGrid>
    </Wrapper>
  );
}
