from flask import Flask, render_template, request, jsonify
import csv
from PIL import Image
import os
import spacy
import base64
from difflib import get_close_matches

nlp = spacy.load("en_core_web_sm")

BASE_IMAGE_DIR = 'Pose'

# Updated recommendations with multi-word diseases and shortforms
recommendations = {
    # Mental Health
    'stress': ['child_s_pose', 'cat-cow_pose'],
    'anxiety': ['breathing_exercises', 'savasana'],
    'depression': ['sun_salutation', 'warrior_i_pose', 'triangle_pose'],
    'insomnia': ['child_s_pose', 'legs_up_the_wall_pose', 'savasana'],
    'ptsd': ['tree_pose', 'mountain_pose', 'eagle_pose'],
    'mental stress': ['child_s_pose', 'cat-cow_pose'],  # Shortform for stress

    # Chronic Pain
    'back_pain': ['knee_to_chest', 'downward_facing_dog_pose'],
    'neck_pain': ['neck_rolls', 'shoulder_rolls', 'arm_circles'],
    'headaches': ['child_s_pose', 'legs_up_the_wall_pose', 'savasana'],
    'arthritis': ['gentle_stretching', 'triangle_pose', 'breathing_exercises'],
    'fibromyalgia': ['child_s_pose', 'gentle_stretching', 'deep_breathing_exercises'],
    'bp': ['knee_to_chest', 'downward_facing_dog_pose'],  # Shortform for back pain

    # Cardiovascular Disease
    'heart_disease': ['deep_breathing_exercises', 'legs_up_the_wall_pose', 'bridge_pose'],
    'high_blood_pressure': ['deep_breathing_exercises', 'reclining_bound_angle_pose', 'bridge_pose'],
    'high_cholesterol': ['sun_salutation', 'warrior_i_pose', 'triangle_pose'],
    'stroke': ['deep_breathing_exercises', 'cat-cow_pose', 'bridge_pose'],
    'hbp': ['deep_breathing_exercises', 'reclining_bound_angle_pose', 'bridge_pose'],  # Shortform for high blood pressure

    # Respiratory Disease
    'asthma': ['deep_breathing_exercises', 'cat-cow_pose', 'bridge_pose'],
    'copd': ['deep_breathing_exercises', 'cat-cow_pose', 'bridge_pose'],
    'bronchitis': ['deep_breathing_exercises', 'cat-cow_pose', 'bridge_pose'],
    'pneumonia': ['deep_breathing_exercises', 'cat-cow_pose', 'bridge_pose'],

    # Digestive Disorders
    'constipation': ['cat-cow_pose', 'twist_pose', 'bridge_pose'],
    'diarrhea': ['child_s_pose', 'legs_up_the_wall_pose', 'savasana'],
    'ibs': ['deep_breathing_exercises', 'twisting_poses', 'bridge_pose'],
    'gerd': ['bridge_pose', 'cat-cow_pose', 'downward_facing_dog_pose'],
    'ulcers': ['child_s_pose', 'legs_up_the_wall_pose', 'savasana'],

    # Hormonal Imbalances
    'menopause': ['deep_breathing_exercises', 'child_s_pose', 'bridge_pose'],
    'thyroid_disorders': ['deep_breathing_exercises', 'shoulder_stand_pose', 'bridge_pose'],
    'pcos': ['deep_breathing_exercises', 'cobra_pose', 'bridge_pose'],
    'pms': ['deep_breathing_exercises', 'child_s_pose', 'bridge_pose'],

    # Autoimmune Diseases
    'lupus': ['deep_breathing_exercises', 'sun_salutation', 'bridge_pose'],
    'rheumatoid_arthritis': ['gentle-stretches', 'savasana', 'breathing_exercises'],
    'multiple_sclerosis': ['gentle-stretches', 'legs_up_the_wall_pose'],
    'hashimotos_thyroiditis': ['deep_breathing_exercises', 'shoulder_stand_pose', 'bridge_pose'],
    'crohns_disease': ['deep_breathing_exercises', 'child_s_pose', 'bridge_pose'],
    'ulcerative_colitis': ['deep_breathing_exercises', 'supine_twist_pose', 'bridge_pose'],
    'ra': ['gentle-stretches', 'savasana', 'breathing_exercises']  # Shortform for rheumatoid arthritis
}

poses = {}

with open('posestepvideo.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        pose_name = row['Pose']
        pose_steps = row['Step']
        pose_video = row['Video']

        poses[pose_name.lower().replace(' ', '_')] = {
            "steps": pose_steps,
            "video": pose_video
        }

def extract_keywords(statement):
    doc = nlp(statement)
    keywords = [token.text.lower() for token in doc if not token.is_stop and token.is_alpha]
    return keywords

def match_multi_word_disease(keywords, recommendations):
    # Check for multi-word diseases and match as a whole
    for disease in recommendations:
        disease_words = disease.split('_')
        if any(all(word in keywords[i:i+len(disease_words)] for i, word in enumerate(disease_words))
               for i in range(len(keywords) - len(disease_words) + 1)):
            return disease
    return None

def get_close_matches_disease(keyword, recommendations):
    # Get the closest matching disease from the recommendations
    diseases = list(recommendations.keys())
    closest_matches = get_close_matches(keyword, diseases, n=1, cutoff=0.8)
    if closest_matches:
        return closest_matches[0]
    return None

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user_input']
    keywords = extract_keywords(user_input)
    print(f"User input: {user_input}")
    print(f"Keywords: {keywords}")

    response_data = []

    # Check for multi-word disease
    disease = match_multi_word_disease(keywords, recommendations)
    print(f"Matched disease: {disease}")

    if disease:
        recommended_poses = recommendations.get(disease)
        response_item = {
            'keyword': disease,
            'recommendations': []
        }
        for pose in recommended_poses:
            try:
                pose_details = poses[pose]
                pose_dir = os.path.join(BASE_IMAGE_DIR, pose)
                if os.path.isdir(pose_dir):
                    img_files = [f for f in os.listdir(pose_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    if img_files:
                        img_path = os.path.join(pose_dir, img_files[0])
                        with open(img_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    else:
                        img_data = None
                else:
                    img_data = None

                recommendation = {
                    'pose': pose,
                    'steps': pose_details['steps'],
                    'video': pose_details['video'],
                    'image_data': img_data
                }
                response_item['recommendations'].append(recommendation)
            except KeyError:
                pass

        response_data.append(response_item)
    else:
        # Check for single-word diseases and shortforms
        for keyword in keywords:
            recommended_poses = recommendations.get(keyword)
            if recommended_poses:
                response_item = {
                    'keyword': keyword,
                    'recommendations': []
                }
                for pose in recommended_poses:
                    try:
                        pose_details = poses[pose]
                        pose_dir = os.path.join(BASE_IMAGE_DIR, pose)
                        if os.path.isdir(pose_dir):
                            img_files = [f for f in os.listdir(pose_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            if img_files:
                                img_path = os.path.join(pose_dir, img_files[0])
                                with open(img_path, 'rb') as img_file:
                                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            else:
                                img_data = None
                        else:
                            img_data = None

                        recommendation = {
                            'pose': pose,
                            'steps': pose_details['steps'],
                            'video': pose_details['video'],
                            'image_data': img_data
                        }
                        response_item['recommendations'].append(recommendation)
                    except KeyError:
                        pass

                response_data.append(response_item)

    # Check for auto-correct suggestions for long user input
    if not response_data:
        user_input_tokens = nlp(user_input)
        for token in user_input_tokens:
            if token.text.lower() not in recommendations:
                closest_match = get_close_matches_disease(token.text.lower(), recommendations)
                if closest_match:
                    recommended_poses = recommendations.get(closest_match)
                    response_item = {
                        'keyword': token.text.lower(),
                        'recommendations': []
                    }
                    for pose in recommended_poses:
                        try:
                            pose_details = poses[pose]
                            pose_dir = os.path.join(BASE_IMAGE_DIR, pose)
                            if os.path.isdir(pose_dir):
                                img_files = [f for f in os.listdir(pose_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                                if img_files:
                                    img_path = os.path.join(pose_dir, img_files[0])
                                    with open(img_path, 'rb') as img_file:
                                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                                else:
                                    img_data = None
                            else:
                                img_data = None

                            recommendation = {
                                'pose': pose,
                                'steps': pose_details['steps'],
                                'video': pose_details['video'],
                                'image_data': img_data
                            }
                            response_item['recommendations'].append(recommendation)
                        except KeyError:
                            pass

                    response_data.append(response_item)

    print(f"Response data: {response_data}")
    if not response_data:
        return render_template('response.html')
    visualization_data = {
        'progress': 75  # Example progress value (replace with actual data)
    }

    return render_template('response.html', response_data=response_data)

if __name__ == '__main__':
    app.run(debug=True)