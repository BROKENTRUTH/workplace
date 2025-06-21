import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from torch.utils.data import Dataset, DataLoader
import os
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# Attempt to import CSVTrafficDataset from pytorch_setup or a common location
try:
    from .pytorch_setup import CSVTrafficDataset # If they are in the same directory
except ImportError:
    logger.warning("Could not import CSVTrafficDataset directly. Defining a local version for anomaly_model.py.") # Changed
    # Define CSVTrafficDataset again if not importable (duplicate for now for subtask)
    # In a real project, this should be in a shared utility module.
    class CSVTrafficDataset(torch.utils.data.Dataset): # Simplified local definition
        def __init__(self, csv_file_path, is_normal_data=True): # Added is_normal_data for training
            self.features = None
            self.is_normal_data = is_normal_data # For autoencoder, train on normal data
            try:
                temp_df = pd.read_csv(csv_file_path)
                # For autoencoder training, we typically don't use labels, only features.
                # If labels exist and is_normal_data is True, we might filter by them.
                if self.is_normal_data and 'label' in temp_df.columns:
                     # Assuming 0 is normal, 1 is anomaly for filtering during training
                    normal_df = temp_df[temp_df['label'] == 0]
                    self.features = torch.tensor(normal_df.drop('label', axis=1).values, dtype=torch.float32)
                    logger.info(f"Loaded NORMAL data for Autoencoder training: {len(self.features)} samples from {csv_file_path}") # Changed
                elif 'label' in temp_df.columns: # Use all data if not specifically normal, or for eval
                    self.features = torch.tensor(temp_df.drop('label', axis=1).values, dtype=torch.float32)
                    logger.info(f"Loaded ALL data (features only): {len(self.features)} samples from {csv_file_path}") # Changed
                else: # No label column
                    self.features = torch.tensor(temp_df.values, dtype=torch.float32)
                    logger.info(f"Loaded data (no labels, assuming all usable for AE): {len(self.features)} samples from {csv_file_path}") # Changed
            except FileNotFoundError:
                logger.error(f"File {csv_file_path} not found.") # Changed
            except Exception as e:
                logger.exception(f"Error loading CSV {csv_file_path}: {e}") # Changed

        def __len__(self): return len(self.features) if self.features is not None else 0
        def __getitem__(self, idx): return self.features[idx], self.features[idx] # Input and target are the same for AE


# --- Development/Educational Purposes Only ---
# Basic Autoencoder for Anomaly Detection.
# This script provides a placeholder for training and evaluation.
# Real-world application requires careful data preprocessing, hyperparameter tuning,
# and robust evaluation strategies (threshold setting, performance metrics).
# --- Development/Educational Purposes Only ---

class Autoencoder(nn.Module):
    def __init__(self, input_dim, encoding_dim):
        super(Autoencoder, self).__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, int(input_dim / 2)),
            nn.ReLU(True),
            nn.Linear(int(input_dim / 2), encoding_dim),
            nn.ReLU(True)
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, int(input_dim / 2)),
            nn.ReLU(True),
            nn.Linear(int(input_dim / 2), input_dim),
            nn.Sigmoid() # Use Sigmoid if input features are normalized between 0 and 1
                         # Or nn.Tanh() if normalized between -1 and 1
                         # Or no activation if features are not bounded like that (but MSE loss is common)
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def train_autoencoder(model: Autoencoder, dataloader: DataLoader, num_epochs: int = 10, learning_rate: float = 1e-3, device: str = 'cpu'):
    """
    Placeholder function to train the Autoencoder model.
    """
    criterion = nn.MSELoss() # Mean Squared Error for reconstruction
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    model.to(device)
    model.train() # Set model to training mode

    logger.info(f"Starting Autoencoder training for {num_epochs} epochs on device: {device}...") # Changed
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0
        for data_batch in dataloader:
            inputs, targets = data_batch # For AE, inputs and targets are the same
            inputs = inputs.to(device)
            targets = targets.to(device)

            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, targets)

            # Backward pass and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1

        avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0
        logger.info(f"Epoch [{epoch+1}/{num_epochs}], Average Reconstruction Loss: {avg_epoch_loss:.6f}") # Changed

    logger.info("Autoencoder training finished.") # Changed
    model.eval() # Set model to evaluation mode after training

def get_reconstruction_errors(model: Autoencoder, dataloader: DataLoader, device: str = 'cpu') -> list:
    """
    Placeholder to calculate reconstruction errors for given data.
    These errors are then used to identify anomalies.
    """
    model.to(device)
    model.eval() # Ensure model is in evaluation mode
    reconstruction_errors = []
    criterion = nn.MSELoss(reduction='none') # Get per-sample error

    logger.info("Calculating reconstruction errors...") # Changed
    with torch.no_grad(): # No need to track gradients
        for data_batch in dataloader:
            inputs, _ = data_batch # We only need inputs for AE error calculation
            inputs = inputs.to(device)
            outputs = model(inputs)

            # Calculate MSE per sample in the batch
            errors = criterion(outputs, inputs).mean(dim=1) # Mean error across features for each sample
            reconstruction_errors.extend(errors.cpu().tolist())

    logger.info(f"Calculated {len(reconstruction_errors)} reconstruction errors.") # Changed
    return reconstruction_errors

def example_usage_anomaly_detection():
    # BasicConfig for logging if this script is run directly.
    if not logger.handlers and not logging.getLogger().handlers: # Avoid adding multiple handlers
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("### Running Anomaly Detection Model (Autoencoder) Placeholder Example ###") # Changed

    # --- 1. Prepare Dummy Data and DataLoader ---
    dummy_data_dir = "dummy_data_ae" # Separate dummy data for AE
    os.makedirs(dummy_data_dir, exist_ok=True)
    dummy_ae_csv_path = os.path.join(dummy_data_dir, "sample_ae_traffic.csv")

    # Create sample data: 10 features, 100 normal samples (label 0), 20 anomaly samples (label 1)
    num_normal = 100
    num_anomaly = 20
    num_features = 10
    data_dict = {f'feature_{i}': torch.rand(num_normal + num_anomaly).tolist() for i in range(num_features)}
    labels = [0]*num_normal + [1]*num_anomaly # Normal first, then anomalies
    data_dict['label'] = labels
    sample_df = pd.DataFrame(data_dict)

    # For Autoencoder, input features should ideally be normalized (e.g., 0-1 for Sigmoid output)
    # Here, torch.rand gives [0,1) which is fine for Sigmoid example.
    sample_df.to_csv(dummy_ae_csv_path, index=False)
    logger.info(f"Created dummy CSV for Autoencoder: {dummy_ae_csv_path}") # Changed

    # Dataset for training (only normal data)
    # The CSVTrafficDataset defined locally will filter for label==0 if is_normal_data=True
    train_dataset = CSVTrafficDataset(csv_file_path=dummy_ae_csv_path, is_normal_data=True)
    if len(train_dataset) == 0:
        logger.error("No normal data loaded for training. Aborting example.") # Changed
        # Clean up dummy file/dir before returning
        try:
            os.remove(dummy_ae_csv_path)
            os.rmdir(dummy_data_dir)
        except OSError:
            pass # Ignore cleanup errors if file wasn't created properly
        return
    train_dataloader = DataLoader(train_dataset, batch_size=16, shuffle=True)

    # Dataset for evaluation (all data - normal and anomalies) to calculate errors
    # The CSVTrafficDataset (local) will load all features if is_normal_data=False (or if no label col)
    eval_dataset = CSVTrafficDataset(csv_file_path=dummy_ae_csv_path, is_normal_data=False)
    if len(eval_dataset) == 0:
        logger.error("No data loaded for evaluation. Aborting example.") # Changed
        # Clean up dummy file/dir
        try:
            os.remove(dummy_ae_csv_path)
            os.rmdir(dummy_data_dir)
        except OSError:
            pass
        return
    eval_dataloader = DataLoader(eval_dataset, batch_size=16, shuffle=False) # No shuffle for eval

    # --- 2. Define and Train Autoencoder Model ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    input_dim = num_features # Should match the number of features in CSV (excluding label)
    encoding_dim = max(1, int(input_dim / 4)) # Example encoding dimension

    ae_model = Autoencoder(input_dim=input_dim, encoding_dim=encoding_dim)

    # Train the model (using only "normal" data from train_dataloader)
    train_autoencoder(ae_model, train_dataloader, num_epochs=5, device=device) # Few epochs for example

    # --- 3. Get Reconstruction Errors ---
    # Get errors for all data (normal and anomalies) using eval_dataloader
    all_reconstruction_errors = get_reconstruction_errors(ae_model, eval_dataloader, device=device)

    # --- 4. Placeholder for Anomaly Thresholding ---
    # In a real scenario, you would analyze the distribution of errors from a
    # held-out normal validation set to set a threshold.
    # Anomalies are data points with errors significantly above this threshold.
    if all_reconstruction_errors:
        # Example: Set a dummy threshold (e.g., 80th percentile of errors on this mixed data for demo)
        # This is NOT the correct way to set a threshold in practice.
        errors_tensor = torch.tensor(all_reconstruction_errors)
        if len(errors_tensor) > 0 : # Check if tensor is not empty
            dummy_threshold = torch.quantile(errors_tensor, 0.80) # 80th percentile as threshold
            logger.info(f"\n--- Anomaly Thresholding (Placeholder) ---") # Changed
            logger.info(f"Dummy Anomaly Threshold (e.g., 80th percentile of errors on mixed data): {dummy_threshold.item():.6f}") # Changed

            num_flagged_anomalies = 0
            logger.info("Sample reconstruction errors (first 25 from eval_dataset) and if flagged:") # Changed

            original_eval_labels = []
            if eval_dataset.data_frame is not None and 'label' in eval_dataset.data_frame.columns:
                 original_eval_labels = eval_dataset.data_frame['label'].tolist()

            for i in range(min(len(all_reconstruction_errors), 25)):
                is_anomaly_flagged = all_reconstruction_errors[i] > dummy_threshold.item()
                if is_anomaly_flagged: num_flagged_anomalies +=1
                original_label_info = f"Original Label={original_eval_labels[i]}" if i < len(original_eval_labels) else "Original Label=N/A"
                logger.info(f"  Data Point {i}: Error={all_reconstruction_errors[i]:.6f}, {original_label_info}, Flagged={is_anomaly_flagged}") # Changed
            logger.info(f"Total data points flagged as anomalies based on dummy threshold: {num_flagged_anomalies} out of {len(all_reconstruction_errors)}") # Changed
        else:
            logger.warning("Reconstruction errors tensor is empty. Cannot calculate threshold.") # Changed
    else:
        logger.warning("No reconstruction errors calculated to demonstrate thresholding.") # Changed

    # --- 5. Cleanup ---
    try:
        os.remove(dummy_ae_csv_path)
        os.rmdir(dummy_data_dir)
        logger.info(f"Cleaned up dummy data: {dummy_ae_csv_path}, {dummy_data_dir}") # Changed
    except OSError as e:
        logger.warning(f"Note: Could not clean up dummy AE data: {e}", exc_info=True) # Changed

    logger.info("\nAnomaly detection model placeholder example finished.") # Changed

if __name__ == "__main__":
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
    logger.info("Starting anomaly_model.py example usage...") # Changed
    example_usage_anomaly_detection()
