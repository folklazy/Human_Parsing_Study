"""Read-only CPI R50 progress; stops/starts no model."""
from rpr_progress import main
if __name__=='__main__':main(model='CPI_R50_CIHP',pointer='CURRENT_CPI_R50_ROUND.txt',controller_script='run_cpi_r50_quality_round.py',worker_script='run_cpi_r50_shared_segment.py')
