import os
import warnings
import torch


def configure_torch_environment():
    """Configure PyTorch environment to minimize warnings and optimize for CPU usage."""
    
    warnings.filterwarnings("ignore", message=".*pin_memory.*")
    warnings.filterwarnings("ignore", message=".*no accelerator.*")
    
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  
    
    torch.set_num_threads(1)  
    
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print("CUDA is available, using GPU")
    else:
        device = torch.device('cpu')
        print("CUDA not available, using CPU")
    
    return device


def get_dataloader_config():
    """Get optimized DataLoader configuration for current environment."""
    
    use_pin_memory = torch.cuda.is_available()
    
    config = {
        'pin_memory': use_pin_memory,
        'num_workers': 0,  
        'batch_size': 16,  
        'persistent_workers': False,  
    }
    
    return config


def suppress_pytorch_warnings():
    """Suppress common PyTorch warnings that don't affect functionality."""
    
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    warnings.filterwarnings("ignore", message=".*pin_memory.*")
    warnings.filterwarnings("ignore", message=".*accelerator.*")
    
    import logging
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)


device = configure_torch_environment()
dataloader_config = get_dataloader_config()
suppress_pytorch_warnings()

print(f"PyTorch configured for device: {device}")
print(f"DataLoader config: {dataloader_config}") 