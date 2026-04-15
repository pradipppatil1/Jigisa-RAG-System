from fastapi import APIRouter, Depends, HTTPException
import os
import pandas as pd
from typing import List, Dict, Any
from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

@router.get("/results", response_model=List[Dict[str, Any]])
def get_evaluation_results(current_user: CurrentUser = Depends(get_current_user)):
    """
    Retrieve the RAGAS ablation study results from the CSV file.
    Only C-Level executives should access this.
    """
    if current_user.role != "c_level":
        raise HTTPException(status_code=403, detail="Not authorized to view evaluation reports.")

    pwd = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.abspath(os.path.join(pwd, "../../data/eval/ablation_results.csv"))

    if not os.path.exists(data_file):
        return []

    try:
        df = pd.read_csv(data_file)
        # Convert DataFrame to list of dicts. Fill na with None.
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation results: {str(e)}")
