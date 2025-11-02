from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import asyncio
from typing import Optional, Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-bot-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

trader_instance: Optional[Any] = None

def create_app(trader):
    global trader_instance
    trader_instance = trader
    return app, socketio

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    if trader_instance:
        status = trader_instance.get_status()
        return jsonify(status)
    return jsonify({'error': 'Trader not initialized'}), 500

@app.route('/api/trades')
def get_trades():
    if trader_instance:
        trades = trader_instance.db_manager.get_trades(limit=50)
        trade_list = []
        for trade in trades:
            trade_list.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'pnl_percentage': trade.pnl_percentage,
                'status': trade.status,
                'confidence': trade.confidence,
                'phase': trade.phase,
                'created_at': trade.created_at.isoformat()
            })
        return jsonify(trade_list)
    return jsonify({'error': 'Trader not initialized'}), 500

@app.route('/api/performance')
def get_performance():
    if trader_instance:
        trades = trader_instance.db_manager.get_trades(limit=500)
        score = trader_instance.scoring_engine.score_trading_performance(trades)
        return jsonify(score)
    return jsonify({'error': 'Trader not initialized'}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
