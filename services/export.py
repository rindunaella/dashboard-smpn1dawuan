from io import BytesIO
import pandas as pd

def dataframe_to_excel(df, sheet_name="Data"):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()
