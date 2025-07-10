import torch
import torch.nn.functional as F
import threading
from pathlib import Path

from .install_maxedout import get_model_files, download, MODEL_DIR

class MXD_UNETLoader:
    @classmethod
    def INPUT_TYPES(cls):
        # Filter curated list for just UNETs in 'diffusion_models'
        curated = get_model_files()
        cls._unet_map = {
            local.split("/")[-1]: (path, local, sha)
            for path, local, sha in curated
            if local.startswith("diffusion_models/")
        }

        return {
            "required": {
                "unet_name": (list(cls._unet_map.keys()),),
                "weight_dtype": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
                ),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "load_unet"
    CATEGORY = "MaxedOut/Loaders"

    def load_unet(self, unet_name, weight_dtype):
        model_options = {}

        if weight_dtype == "fp8_e4m3fn":
            model_options["dtype"] = torch.float8_e4m3fn
        elif weight_dtype == "fp8_e4m3fn_fast":
            model_options["dtype"] = torch.float8_e4m3fn
            model_options["fp8_optimizations"] = True
        elif weight_dtype == "fp8_e5m2":
            model_options["dtype"] = torch.float8_e5m2

        # Resolve full HuggingFace path and expected hash
        hf_path, local_rel_path, expected_sha = self._unet_map[unet_name]
        local_path = MODEL_DIR / local_rel_path

        # Ensure model exists, download if needed
        if not local_path.exists():
            print(f"🔽 Downloading {unet_name} ...")
            download(hf_path, local_path, expected_sha)
        else:
            print(f"✅ {unet_name} found. Skipping download.")

        # Load the UNET model using ComfyUI utils
        model = comfy.sd.load_diffusion_model(str(local_path), model_options=model_options)
        return (model,)
    
####################################################################################################################################################


# NODE MAPPING
NODE_CLASS_MAPPINGS = {
    "MXD_UNETLoader": MXD_UNETLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MXD_UNETLoader": "Load UNET MXD",
}