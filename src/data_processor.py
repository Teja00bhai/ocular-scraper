"""
Data processing and SOV calculation for Zepto API data
"""
import os
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
from src.config import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "data_processor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataProcessor")

class ZeptoDataProcessor:
    """
    Process extracted Zepto data and calculate SOV metrics
    """
    
    def __init__(self, output_dir: str = "outputs"):
        """Initialize the data processor"""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def process_json_files(self, json_dir: Optional[str] = None) -> pd.DataFrame:
        """Process all JSON files in the specified directory
        
        Args:
            json_dir: Directory containing JSON files (defaults to self.output_dir)
            
        Returns:
            DataFrame with extracted product information
        """
        if json_dir is None:
            json_dir = self.output_dir
            
        all_products = []
        import json
        import glob
        
        # Find all JSON files in the directory
        json_files = glob.glob(os.path.join(json_dir, "*_results.json"))
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            try:
                # Extract keyword from filename
                filename = os.path.basename(json_file)
                keyword = filename.replace("_results.json", "").replace("_", " ")
                
                # Load JSON data
                with open(json_file, 'r') as f:
                    api_response = json.load(f)
                
                # Extract products from this response
                products = self.extract_products_from_api_response(api_response, keyword)
                all_products.extend(products)
                
            except Exception as e:
                logger.error(f"Error processing file {json_file}: {e}")
        
        # Convert to DataFrame
        if all_products:
            df = pd.DataFrame(all_products)
            logger.info(f"Processed {len(all_products)} products from {len(json_files)} JSON files")
            return df
        else:
            logger.warning("No products extracted from JSON files")
            return pd.DataFrame()
    
    def extract_products_from_api_response(self, api_response: Dict[str, Any], keyword: str, region: str = "default") -> List[Dict[str, Any]]:
        """Extract structured product information from Zepto API response
        
        Args:
            api_response: Raw API response from Zepto search
            keyword: Search keyword used
            region: Region/location for the search
            
        Returns:
            List of product dictionaries with structured information
        """
        products = []
        
        try:
            # Check if the response has the expected structure
            if not api_response or "layout" not in api_response:
                logger.warning(f"Invalid API response format for keyword '{keyword}'")
                return products
                
            # Process each widget in the layout
            for widget in api_response.get("layout", []):
                # Look for product grid widgets
                if widget.get("widgetId", "").startswith("PRODUCT_GRID") or widget.get("widgetName", "").startswith("PRODUCT_GRID"):
                    # Extract product data from resolver
                    resolver_data = widget.get("data", {}).get("resolver", {}).get("data", {})
                    items = resolver_data.get("items", [])
                    
                    # Process each product item
                    for position, item in enumerate(items):
                        product_data = {}
                        
                        # Extract basic product info
                        product_data["search_keyword"] = keyword
                        product_data["region"] = region
                        product_data["position"] = position
                        
                        # Extract product details
                        product = item.get("product", {})
                        product_data["product_id"] = product.get("productId", "")
                        product_data["product_name"] = product.get("name", "")
                        product_data["brand"] = product.get("brand", "")
                        product_data["category"] = product.get("primaryCategoryName", "")
                        product_data["image_url"] = product.get("imageUrl", "")
                        product_data["product_url"] = f"https://www.zeptonow.com/product/{product.get('productId', '')}" if product.get("productId") else ""
                        
                        # Extract pricing information
                        product_data["mrp"] = item.get("mrp", 0) / 100 if item.get("mrp") else 0  # Convert to rupees
                        product_data["selling_price"] = item.get("discountedSellingPrice", 0) / 100 if item.get("discountedSellingPrice") else 0
                        product_data["discount_percent"] = item.get("discountPercent", 0)
                        
                        # Extract additional information
                        product_data["is_in_stock"] = not item.get("outOfStock", True)
                        product_data["available_quantity"] = item.get("availableQuantity", 0)
                        
                        # Extract rating information
                        rating_summary = product.get("ratingSummary", {})
                        product_data["average_rating"] = rating_summary.get("averageRating", 0)
                        product_data["total_ratings"] = rating_summary.get("totalRatings", 0)
                        
                        # Check if product is sponsored/promoted
                        product_data["is_sponsored"] = False
                        if "campaignType" in item or "campaignId" in item:
                            product_data["is_sponsored"] = True
                        
                        # Extract product attributes
                        product_data["weight"] = product.get("weightInGms", 0)
                        product_data["pack_size"] = product.get("packsize", "")
                        product_data["unit_of_measure"] = product.get("unitOfMeasure", "")
                        product_data["nutritional_info"] = product.get("nutritionalInfo", "")
                        
                        products.append(product_data)
                        
            logger.info(f"Extracted {len(products)} products for keyword '{keyword}'")
            
        except Exception as e:
            logger.error(f"Error extracting products from API response: {e}")
            
        return products
    
    def process_extracted_data(self, raw_data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
        """Process raw data and calculate SOV metrics"""
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        if df.empty:
            logger.warning("No data extracted")
            return None
        
        # Calculate SOV by keyword
        sov_results = []
        
        # Group by keyword and region for analysis
        for keyword in df['search_keyword'].unique():
            for region in df['region'].unique():
                # Filter data for this keyword and region
                filtered_data = df[(df['search_keyword'] == keyword) & (df['region'] == region)]
                
                if filtered_data.empty:
                    continue
                
                # Brand-wise product count
                brand_counts = filtered_data['brand'].value_counts()
                total_products = len(filtered_data)
                
                # Position-weighted SOV
                brand_weighted_scores = filtered_data.groupby('brand').apply(
                    lambda x: sum(1/(pos+1) for pos in x['position'] if pos >= 0)
                )
                total_weighted_score = brand_weighted_scores.sum()
                
                for brand in brand_counts.index:
                    sov_results.append({
                        'keyword': keyword,
                        'region': region,
                        'brand': brand,
                        'product_count': brand_counts[brand],
                        'sov_percentage': round((brand_counts[brand] / total_products) * 100, 2),
                        'weighted_sov': round((brand_weighted_scores[brand] / total_weighted_score) * 100, 2) 
                            if total_weighted_score > 0 else 0,
                        'avg_position': round(filtered_data[filtered_data['brand'] == brand]['position'].mean(), 2),
                        'avg_rating': round(filtered_data[filtered_data['brand'] == brand]['average_rating'].mean(), 2),
                        'avg_price': round(filtered_data[filtered_data['brand'] == brand]['selling_price'].mean(), 2),
                        'sponsored_count': filtered_data[(filtered_data['brand'] == brand) & 
                                                        (filtered_data['is_sponsored'] == True)].shape[0]
                    })
        
        logger.info(f"Generated SOV analysis with {len(sov_results)} brand-keyword combinations")
        return pd.DataFrame(sov_results)
    
    def save_results(self, products_df: pd.DataFrame, sov_df: pd.DataFrame) -> Tuple[str, str]:
        """Save results to CSV files"""
        timestamp = int(time.time())
        
        # Save detailed product data
        products_file = f"{self.output_dir}/zepto_products_{timestamp}.csv"
        products_df.to_csv(products_file, index=False)
        
        # Save SOV analysis
        sov_file = f"{self.output_dir}/sov_analysis_{timestamp}.csv" 
        sov_df.to_csv(sov_file, index=False)
        
        logger.info(f"Results saved to {products_file} and {sov_file}")
        
        return products_file, sov_file
    
    def generate_summary_report(self, products_df: pd.DataFrame, sov_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a summary report of the extraction and analysis"""
        
        summary = {
            "total_products": len(products_df),
            "unique_keywords": products_df['search_keyword'].nunique(),
            "unique_brands": products_df['brand'].nunique(),
            "regions_covered": products_df['region'].nunique(),
            "top_brands_by_count": products_df['brand'].value_counts().head(5).to_dict(),
            "top_brands_by_sov": sov_df.groupby('brand')['weighted_sov'].mean().sort_values(ascending=False).head(5).to_dict(),
            "extraction_timestamp": time.time()
        }
        
        # Save summary to file
        timestamp = int(time.time())
        summary_file = f"{self.output_dir}/summary_report_{timestamp}.json"
        
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=4)
        
        logger.info(f"Summary report saved to {summary_file}")
        
        return summary
