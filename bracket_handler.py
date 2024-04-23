from src.paper_trading.alpaca_manager import AlpacaManager
import asyncio
import datetime


class BracketManager:
    def __init__(self):
        self.alpaca_manager = AlpacaManager()

    def run(self):
        asyncio.run(self.handle_exit_via_PL())

    async def handle_exit_via_PL(self):
        while True:
            await asyncio.sleep(60)
            print('checking open positions', datetime.datetime.now())
            try:
                positions = self.alpaca_manager.get_positions()
                for position in positions:
                    print('checking position', position.symbol)
                    entry_price = position.avg_entry_price
                    take_profit_price = round(
                        float(entry_price) * 1.005, 2)
                    stop_loss_price = round(float(entry_price) * .998, 2)
                    current_price = float(position.current_price)
                    if (current_price > take_profit_price):
                        print('price is higher than take profit exiting',
                              position.symbol, 'Profit', position.unrealized_pl)
                        self.alpaca_manager.close_position_by_symbol(
                            position.symbol)
                        return

                    elif (current_price < stop_loss_price):
                        print('price is lower than stop loss exiting',
                              position.symbol, 'Loss', position.unrealized_pl)
                        self.alpaca_manager.close_position_by_symbol(
                            position.symbol)
                        return
                    print('no action taken on', position.symbol)

            except Exception as e:
                print('error handling open positions', e)
                return


asyncio.run(BracketManager().handle_exit_via_PL())
