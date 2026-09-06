import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import os

class FloodLSTM:
    def __init__(self, lookback=10, n_features=1):
        self.lookback = lookback  # Số ngày quá khứ dùng để dự báo
        self.n_features = n_features
        self.model = None
        self.scaler = MinMaxScaler()
    
    def prepare_data(self, data, target_col='water_level'):
        """
        Chuyển dữ liệu thành dạng chuỗi để train LSTM
        data: DataFrame chứa cột water_level (và có thể các biến khác)
        """
        # Nếu có nhiều cột, chỉ lấy cột dự báo
        if isinstance(data, pd.DataFrame):
            values = data[[target_col]].values
        else:
            values = np.array(data).reshape(-1, 1)
        
        # Chuẩn hóa dữ liệu về [0,1]
        scaled = self.scaler.fit_transform(values)
        
        X, y = [], []
        for i in range(self.lookback, len(scaled)):
            X.append(scaled[i-self.lookback:i])
            y.append(scaled[i, 0])
        
        X = np.array(X)
        y = np.array(y)
        return X, y
    
    def build_model(self, input_shape):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        self.model = model
        return model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32):
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=0  # Im lặng khi train (có thể đổi 1 để xem)
        )
        return history
    
    def predict_future(self, last_sequence, steps=7):
        """
        Dự báo chuỗi trong tương lai (steps ngày)
        last_sequence: mảng shape (lookback, n_features)
        """
        predictions = []
        current_seq = last_sequence.copy()
        
        for _ in range(steps):
            pred = self.model.predict(current_seq.reshape(1, self.lookback, self.n_features), verbose=0)
            predictions.append(pred[0, 0])
            # Cập nhật chuỗi: bỏ giá trị đầu, thêm dự báo mới
            current_seq = np.roll(current_seq, -1, axis=0)
            current_seq[-1] = pred[0]
        
        # Chuyển về thang đo ban đầu
        pred_array = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(pred_array).flatten()
    
    def save_model(self, model_path='data/models/flood_lstm.h5', scaler_path='data/models/flood_scaler.pkl'):
        self.model.save(model_path)
        joblib.dump(self.scaler, scaler_path)
    
    def load_model(self, model_path='data/models/flood_lstm.h5', scaler_path='data/models/flood_scaler.pkl'):
        from tensorflow.keras.models import load_model
        self.model = load_model(model_path)
        self.scaler = joblib.load(scaler_path)

# ===============================
# TẠO DỮ LIỆU MẪU ĐỂ DEMO
# ===============================
def generate_sample_data(n_days=365, start_level=5.0):
    """
    Tạo dữ liệu mực nước giả với chu kỳ mùa và nhiễu
    """
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=n_days)
    # Mô phỏng mực nước theo mùa + nhiễu
    seasonal = 2 * np.sin(2 * np.pi * np.arange(n_days) / 90)  # Chu kỳ 90 ngày
    noise = np.random.normal(0, 0.3, n_days)
    trend = np.linspace(0, 0.5, n_days)  # Xu hướng dâng nhẹ
    water_level = start_level + seasonal + noise + trend
    # Đảm bảo không âm
    water_level = np.maximum(water_level, 1.0)
    
    df = pd.DataFrame({
        'date': dates,
        'water_level': water_level
    })
    return df