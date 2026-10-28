"""Read-only ConvNeXt-B progress, no model imports or process controls."""
from rpr_progress import main
if __name__=="__main__":main(model="CPI_ConvNeXtB_CIHP",pointer="CURRENT_CPI_CONVNEXT_ROUND.txt",controller_script="run_cpi_convnext_quality_round.py",worker_script="run_cpi_convnext_shared_segment.py")
