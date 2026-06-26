import sys
import time

print("Starting PyTorch import test...")
t0 = time.time()
import torch
print(f"Imported torch in {time.time() - t0:.2f} seconds.")

print("Checking CUDA availability...")
t0 = time.time()
cuda_avail = torch.cuda.is_available()
print(f"CUDA available: {cuda_avail} (checked in {time.time() - t0:.2f} seconds).")

if cuda_avail:
    print("CUDA Device Name:", torch.cuda.get_device_name(0))
    print("CUDA Device Count:", torch.cuda.device_count())
