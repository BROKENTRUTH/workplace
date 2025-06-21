import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import pandas as pd
import os
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import numpy as np
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# Attempt to import CSVTrafficDataset and SimpleMLP from pytorch_setup or a common location
try:
    from .pytorch_setup import CSVTrafficDataset as PytorchSetupCSVTrafficDataset, SimpleMLP
except ImportError:
    logger.warning("Could not import from .pytorch_setup. Defining local versions for classification_model.py.") # Changed
    # Define SimpleMLP again (duplicate for now for subtask if not importable)
    class SimpleMLP(nn.Module):
        def __init__(self, input_size, hidden_size, num_classes):
            super(SimpleMLP, self).__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, num_classes)
        def forward(self, x):
            out = self.fc1(x); out = self.relu(out); out = self.fc2(out)
            return out

    # Define CSVTrafficDataset again (adapted for classification - needs labels)
    class PytorchSetupCSVTrafficDataset(torch.utils.data.Dataset):
        def __init__(self, csv_file_path): # Removed is_normal_data for general classification
            self.features = None
            self.labels = None
            try:
                temp_df = pd.read_csv(csv_file_path)
                if 'label' not in temp_df.columns:
                    logger.error("Label column not found in CSV for classification.") # Changed
                    raise ValueError("Label column not found in CSV for classification.")
                self.labels = torch.tensor(temp_df['label'].values, dtype=torch.long) # CrossEntropyLoss expects long
                self.features = torch.tensor(temp_df.drop('label', axis=1).values, dtype=torch.float32)
                logger.info(f"Loaded data for Classification: {len(self.features)} samples from {csv_file_path}") # Changed
            except FileNotFoundError:
                logger.error(f"File {csv_file_path} not found.") # Changed
            except Exception as e:
                logger.exception(f"Error loading CSV {csv_file_path}: {e}") # Changed

        def __len__(self): return len(self.features) if self.features is not None else 0
        def __getitem__(self, idx): return self.features[idx], self.labels[idx]


# --- Development/Educational Purposes Only ---
# Basic MLP for Threat Classification.
# This script provides a placeholder for training and evaluation.
# Real-world application requires careful data preprocessing, feature engineering,
# hyperparameter tuning, robust evaluation, and handling of imbalanced classes.
# --- Development/Educational Purposes Only ---

def train_classifier(model: nn.Module, dataloader: DataLoader, num_epochs: int = 10, learning_rate: float = 1e-3, device: str = 'cpu', class_weights: torch.Tensor = None):
    """
    Placeholder function to train the classification model.
    """
    if class_weights is not None:
        class_weights = class_weights.to(device)
    # CrossEntropyLoss combines LogSoftmax and NLLLoss - good for multi-class
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    model.to(device)
    model.train() # Set model to training mode

    logger.info(f"Starting Classifier training for {num_epochs} epochs on device: {device}...") # Changed
    if class_weights is not None:
        logger.info(f"Using class weights: {class_weights.cpu().tolist()}") # Changed

    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0
        all_preds = []
        all_targets = []

        for features, labels in dataloader:
            features = features.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(features) # Raw logits
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1

            # For accuracy calculation during epoch (optional)
            _, predicted_classes = torch.max(outputs, 1)
            all_preds.extend(predicted_classes.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())

        avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0
        epoch_accuracy = accuracy_score(all_targets, all_preds) if all_targets else 0
        logger.info(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_epoch_loss:.4f}, Accuracy: {epoch_accuracy:.4f}") # Changed

    logger.info("Classifier training finished.") # Changed
    model.eval() # Set model to evaluation mode

def evaluate_classifier(model: nn.Module, dataloader: DataLoader, device: str = 'cpu'):
    """
    Placeholder to evaluate the classifier.
    Prints accuracy, precision, recall, F1-score, and confusion matrix.
    """
    model.to(device)
    model.eval()

    all_predictions = []
    all_true_labels = []

    logger.info("\nEvaluating classifier...") # Changed
    with torch.no_grad():
        for features, labels in dataloader:
            features = features.to(device)
            labels = labels.to(device)

            outputs = model(features)
            _, predicted_classes = torch.max(outputs, 1) # Get the index of the max log-probability

            all_predictions.extend(predicted_classes.cpu().numpy())
            all_true_labels.extend(labels.cpu().numpy())

    if not all_true_labels:
        logger.warning("No data to evaluate.") # Changed
        return

    accuracy = accuracy_score(all_true_labels, all_predictions)
    # average='weighted' for imbalanced classes, or None for per-class
    precision, recall, f1, _ = precision_recall_fscore_support(all_true_labels, all_predictions, average='weighted', zero_division=0)
    # For per-class metrics: precision_recall_fscore_support(all_true_labels, all_predictions, average=None)

    cm = confusion_matrix(all_true_labels, all_predictions)

    logger.info(f"Overall Accuracy: {accuracy:.4f}") # Changed
    logger.info(f"Weighted Precision: {precision:.4f}") # Changed
    logger.info(f"Weighted Recall: {recall:.4f}") # Changed
    logger.info(f"Weighted F1-Score: {f1:.4f}") # Changed
    logger.info("Confusion Matrix:\n" + str(cm)) # Changed
    logger.info("Note: For imbalanced datasets, focus on per-class metrics, PR AUC, and ROC AUC.") # Changed

def calculate_class_weights(labels: list) -> torch.Tensor:
    """
    Calculates class weights for imbalanced datasets.
    Weight for a class = Total Samples / (Number of Classes * Samples in Class)
    """
    if not labels: return None
    labels_array = np.array(labels)
    num_classes = len(np.unique(labels_array))
    total_samples = len(labels_array)

    weights = []
    for i in range(num_classes):
        class_samples = np.sum(labels_array == i)
        if class_samples > 0:
            weights.append(total_samples / (num_classes * class_samples))
        else:
            logger.warning(f"Class {i} not found in labels for weight calculation. Assigning default weight 1.0.") # Changed
            weights.append(1.0)

    return torch.tensor(weights, dtype=torch.float32)


def example_usage_classification():
    # BasicConfig for logging if this script is run directly.
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("### Running Threat Classification Model (MLP) Placeholder Example ###") # Changed

    # --- 1. Prepare Dummy Data and DataLoader ---
    dummy_data_dir = "dummy_data_clf" # Separate dummy data for classifier
    os.makedirs(dummy_data_dir, exist_ok=True)
    dummy_clf_csv_path = os.path.join(dummy_data_dir, "sample_clf_traffic.csv")

    # Create sample data: 10 features, 3 classes (0: normal, 1: typeA, 2: typeB)
    # Imbalanced: class 0 (70%), class 1 (20%), class 2 (10%)
    num_features = 10
    n_c0, n_c1, n_c2 = 70, 20, 10
    total_samples = n_c0 + n_c1 + n_c2

    data_dict = {f'feature_{i}': torch.randn(total_samples).tolist() for i in range(num_features)}
    labels = [0]*n_c0 + [1]*n_c1 + [2]*n_c2
    data_dict['label'] = labels
    sample_df = pd.DataFrame(data_dict)
    sample_df.to_csv(dummy_clf_csv_path, index=False)
    logger.info(f"Created dummy CSV for Classifier: {dummy_clf_csv_path} with classes 0,1,2.") # Changed

    # For this example, we'll use the same CSV for train and "test" (evaluation)
    # In practice, use separate, properly split datasets.
    full_dataset = PytorchSetupCSVTrafficDataset(csv_file_path=dummy_clf_csv_path)
    if len(full_dataset) == 0:
        logger.error("No data loaded. Aborting example.") # Changed
        # Clean up dummy file/dir before returning
        try:
            os.remove(dummy_clf_csv_path)
            os.rmdir(dummy_data_dir)
        except OSError:
            pass # Ignore cleanup errors if file wasn't created properly
        return

    # Calculate class weights from the full dataset for handling imbalance
    # In practice, calculate from training set only.
    class_weights = calculate_class_weights(sample_df['label'].tolist())

    # Using the same dataset for train and eval for simplicity here
    train_dataloader = DataLoader(full_dataset, batch_size=16, shuffle=True)
    eval_dataloader = DataLoader(full_dataset, batch_size=16, shuffle=False)


    # --- 2. Define and Train Classifier Model ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    input_dim = num_features
    num_classes = len(sample_df['label'].unique()) # Determine num_classes from data

    # Use SimpleMLP from pytorch_setup (or local definition)
    clf_model = SimpleMLP(input_dim=input_dim, hidden_size=32, num_classes=num_classes)

    train_classifier(clf_model, train_dataloader, num_epochs=5, device=device, class_weights=class_weights)

    # --- 3. Evaluate Classifier ---
    evaluate_classifier(clf_model, eval_dataloader, device=device)

    # --- 4. Cleanup ---
    try:
        os.remove(dummy_clf_csv_path)
        os.rmdir(dummy_data_dir)
        logger.info(f"Cleaned up dummy CLF data: {dummy_clf_csv_path}, {dummy_data_dir}") # Changed
    except OSError as e:
        logger.warning(f"Note: Could not clean up dummy CLF data: {e}", exc_info=True) # Changed

    logger.info("\nThreat classification model placeholder example finished.") # Changed

if __name__ == "__main__":
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
    logger.info("Starting classification_model.py example usage...") # Changed
    example_usage_classification()
