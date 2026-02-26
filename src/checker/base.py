from abc import ABC, abstractmethod
from typing import List, Union
import pandas as pd
from datetime import date, datetime

class DataChecker(ABC):
    """
    Abstract Base Class for Data Integrity Checking.
    """

    @abstractmethod
    def check_continuity(
        self, 
        data: pd.DataFrame, 
        start: Union[date, datetime], 
        end: Union[date, datetime], 
        calendar: List[date]
    ) -> List[str]:
        """
        Check for missing dates in the given range.
        Returns a list of missing dates as strings.
        """
        pass

    @abstractmethod
    def check_outliers(
        self, 
        data: pd.DataFrame, 
        threshold: float = 0.2
    ) -> pd.DataFrame:
        """
        Check for price jumps greater than the threshold (default 20%).
        Returns rows that are outliers.
        """
        pass

    @abstractmethod
    def check_volume(
        self, 
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Check for zero volume on trading days.
        """
        pass
