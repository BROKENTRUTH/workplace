import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from torch.utils.data import Dataset, DataLoader
import os

# --- Development/Educational Purposes Only ---
# This script demonstrates basic PyTorch setup:
# - Tensor operations
# - A simple MLP model definition
# - A placeholder for a custom Dataset and DataLoader for CSVs
# Actual model training and data processing would be more complex.
# --- Development/Educational Purposes Only ---

def demonstrate_tensor_operations():
    print("### Demonstrating PyTorch Tensor Operations ###")
    # Create tensors
    x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    y = torch.rand(2, 2)

    print(f"Tensor x:\n{x}")
    print(f"Tensor y:\n{y}")

    # Operations
    z_add = x + y
    z_mul = x * y

    print(f"x + y:\n{z_add}")
    print(f"x * y:\n{z_mul}")

    # Check for GPU availability
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"CUDA (GPU) is available. Moving tensors to {device}.")
        x_cuda = x.to(device)
        y_cuda = y.to(device)
        z_cuda_add = x_cuda + y_cuda
        print(f"x_cuda + y_cuda on GPU:\n{z_cuda_add}")
    else:
        device = torch.device("cpu")
        print("CUDA (GPU) not available, using CPU.")
    print("-" * 30)
    return device

# Define a simple MLP model
class SimpleMLP(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(SimpleMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)
        # For binary classification, num_classes=1 and Sigmoid output
        # For multi-class, num_classes > 1 and often no explicit output activation here
        # as CrossEntropyLoss combines LogSoftmax and NLLLoss.

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

def demonstrate_model_definition(input_size=10, device='cpu'):
    print("\n### Demonstrating Simple MLP Model Definition ###")
    model = SimpleMLP(input_size=input_size, hidden_size=32, num_classes=2) # Example: 2 classes
    model.to(device) # Move model to device
    print(model)

    # Example dummy input
    # Batch size of 5, input_size features
    dummy_input = torch.randn(5, input_size).to(device)
    try:
        output = model(dummy_input)
        print(f"Dummy input shape: {dummy_input.shape}")
        print(f"Model output shape: {output.shape}")
    except Exception as e:
        print(f"Error during model forward pass: {e}")
    print("-" * 30)


# Placeholder for CSV Dataset and DataLoader
class CSVTrafficDataset(Dataset):
    def __init__(self, csv_file_path, transform=None):
        self.data_frame = None
        self.labels = None # Assuming a 'label' column exists
        self.features = None

        # In a real scenario, implement robust file reading and preprocessing
        try:
            # For demonstration, assume a simple structure
            # In reality, you'd handle feature selection, type conversion, etc.
            temp_df = pd.read_csv(csv_file_path)
            if 'label' in temp_df.columns:
                self.labels = torch.tensor(temp_df['label'].values, dtype=torch.float32) # Or long for CrossEntropy
                self.features = torch.tensor(temp_df.drop('label', axis=1).values, dtype=torch.float32)
            else: # Unsupervised case perhaps, or labels are separate
                self.features = torch.tensor(temp_df.values, dtype=torch.float32)

            self.data_frame = temp_df # Keep for reference if needed
            print(f"Successfully loaded and processed {csv_file_path}")
            if self.labels is not None:
                print(f"Found {len(self.features)} samples and {len(self.labels)} labels.")
            else:
                print(f"Found {len(self.features)} samples (no 'label' column detected).")

        except FileNotFoundError:
            print(f"Error: The file {csv_file_path} was not found.")
        except pd.errors.EmptyDataError:
            print(f"Error: The file {csv_file_path} is empty.")
        except Exception as e:
            print(f"Error loading CSV {csv_file_path}: {e}")

        self.transform = transform

    def __len__(self):
        return len(self.features) if self.features is not None else 0

    def __getitem__(self, idx):
        sample_features = self.features[idx]
        sample_label = self.labels[idx] if self.labels is not None else -1 # Dummy label if none

        if self.transform: # e.g., for specific augmentations, not common for tabular
            sample_features = self.transform(sample_features)

        if self.labels is not None:
            return sample_features, sample_label
        else:
            return sample_features # For unsupervised

def demonstrate_data_loading():
    print("\n### Demonstrating Placeholder Data Loading ###")
    # Create a dummy CSV file for demonstration
    dummy_data_dir = "dummy_data"
    os.makedirs(dummy_data_dir, exist_ok=True)
    dummy_csv_path = os.path.join(dummy_data_dir, "sample_traffic.csv")

    # Create sample data: 10 features, 1 label column, 100 rows
    sample_df_data = {f'feature_{i}': torch.randn(100).tolist() for i in range(10)}
    sample_df_data['label'] = (torch.rand(100) > 0.8).int().tolist() # ~20% positive class
    sample_df = pd.DataFrame(sample_df_data)
    sample_df.to_csv(dummy_csv_path, index=False)
    print(f"Created dummy CSV: {dummy_csv_path}")

    # Instantiate dataset and dataloader
    # In a real scenario, you'd have separate train/val/test CSVs or split one
    traffic_dataset = CSVTrafficDataset(csv_file_path=dummy_csv_path)

    if len(traffic_dataset) > 0:
        # Batch size of 32, shuffle true for training
        traffic_dataloader = DataLoader(traffic_dataset, batch_size=32, shuffle=True)

        # Iterate over a few batches
        print("Iterating through DataLoader (first few batches):")
        for i, batch in enumerate(traffic_dataloader):
            if i >= 2: # Show first 2 batches
                break
            features, labels = batch
            print(f"Batch {i+1}:")
            print(f"  Features shape: {features.shape}") # [batch_size, num_features]
            print(f"  Labels shape: {labels.shape}")     # [batch_size]
            print(f"  First feature vector in batch: {features[0][:5]}...") # Print first 5 values
            print(f"  First label in batch: {labels[0]}")
    else:
        print("Skipping DataLoader demonstration as dataset is empty or failed to load.")

    # Clean up dummy file/dir
    # try:
    #     os.remove(dummy_csv_path)
    #     os.rmdir(dummy_data_dir)
    #     print(f"Cleaned up dummy data: {dummy_csv_path}, {dummy_data_dir}")
    # except OSError as e:
    #     print(f"Error cleaning up dummy data: {e}")
    print("-" * 30)


if __name__ == "__main__":
    print("--- Initial PyTorch Setup for AI Threat Detection ---")
    current_device = demonstrate_tensor_operations()
    demonstrate_model_definition(device=current_device)
    demonstrate_data_loading()
    print("PyTorch setup demonstration finished.")
