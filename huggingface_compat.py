#!/usr/bin/env python3
"""Comprehensive compatibility patches for huggingface_hub"""

import sys
import importlib

def apply_huggingface_patches():
    """Apply all necessary huggingface compatibility patches"""
    
    # Patch 1: PyTorch pytree compatibility
    try:
        import torch.utils._pytree as pytree
        if not hasattr(pytree, 'register_pytree_node') and hasattr(pytree, '_register_pytree_node'):
            pytree.register_pytree_node = pytree._register_pytree_node
            print("✅ Applied PyTorch pytree patch")
    except:
        pass
    
    # Patch 2: huggingface_hub split_torch_state_dict_into_shards
    try:
        import huggingface_hub
        from huggingface_hub import __version__
        print(f"🤗 huggingface_hub version: {__version__}")
        
        # For versions >= 0.20, the function might be in a different module
        if not hasattr(huggingface_hub, 'split_torch_state_dict_into_shards'):
            try:
                from huggingface_hub.utils import safe_serialization
                if hasattr(safe_serialization, 'split_torch_state_dict_into_shards'):
                    huggingface_hub.split_torch_state_dict_into_shards = safe_serialization.split_torch_state_dict_into_shards
                    print("✅ Applied split_torch_state_dict_into_shards patch")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Could not apply huggingface patches: {e}")

# Apply patches immediately when imported
apply_huggingface_patches()