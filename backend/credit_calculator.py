from models import CreditConfig

credit_config = CreditConfig()

def calculate_credit_cost(design_key: str, features: list) -> dict:
    """Calculate total credit cost for a wedding"""
    design_cost = credit_config.designs.get(design_key, 0)
    
    features_cost = 0
    feature_breakdown = {}
    
    for feature in features:
        cost = credit_config.features.get(feature, 0)
        features_cost += cost
        feature_breakdown[feature] = cost
    
    total_cost = design_cost + features_cost
    
    return {
        "design_cost": design_cost,
        "features_cost": features_cost,
        "total_cost": total_cost,
        "breakdown": {
            "design": {design_key: design_cost},
            "features": feature_breakdown
        }
    }