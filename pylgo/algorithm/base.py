from datetime import datetime
import logging
import pandas as pd
from ..data_loader import Loader, History
from ..portfolio import Portfolio, Position
from .time_simulation import TimeSimulation
from abc import ABC, abstractmethod
# TODO add multiple symbols.
# TODO add confifuration file
logger = logging.getLogger('algorithm testing')
logger.setLevel(logging.DEBUG)


class AlgorithmBase(ABC):
    algo_name = None

    def __init__(self, symbol=None, prefix=None, frequency=None, start=None, end=None, reporting_path=None, cash=10_000) -> None:
        self.symbol = symbol
        # Allow lower frequencies
        self.start = start
        self.end = end
        self.frequency = frequency
        self.prefix = prefix
        self.cash = cash
        self.portfolio = Portfolio(cash)
        self.reporting_path = f'{reporting_path}/{self.symbol}_{self.frequency}_{self.start}_{self.end}_{int(datetime.now().timestamp())}.txt'
        self.file_handler = logging.FileHandler(self.reporting_path)
        self.file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler.setFormatter(formatter)
        logger.addHandler(self.file_handler)
        logger.warning('Starting algorithm.')

    def map_signals(self, signals, data):
        # TODO here should be market data
        positions = []
        if not data.empty:
            price = data.iloc[-1]['close']
            for signal in signals:
                if self.symbol in [x.symbol for x in self.portfolio.active_positions]:
                    self.portfolio.active_positions[0].current_price = price
                if signal.signal_type == 1:
                    # TODO make generic
                    qnty = self.cash / price
                    positions.append(
                        Position(self.symbol, qnty, price))
        return positions

    def run(self):
        data = Loader(self.symbol,
                      self.frequency, self.start, self.end, self.prefix).load()
        history = History(data)
        simulation = TimeSimulation(
            self.frequency, self.start, self.end, history.last_point)
        while not simulation.stop():
            current_data = history.get_all_available_data(
                simulation.current_time)
            signals = self.create_signals(current_data)
            new_orders = self.map_signals(signals, current_data)
            self.portfolio.update(new_orders)
            simulation.update_current_timestamp()
        logger.info('Algorithm finished %s.', self.algo_name)
        logger.info('Total cash: %s', self.portfolio.cash)
        logger.info('Total value: %s', self.portfolio.total_value)
        logger.info('Total return: %s', self.portfolio.portfolio_return)

    @abstractmethod
    def create_signals(self, data):
        pass
