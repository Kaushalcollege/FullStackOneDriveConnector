import React from "react";
import "./FormField.css";

const FormField = ({ label, placeholder, value, onChange }) => {
  return (
    <label>
      {label}
      <input
        className="input-field"
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
};

export default FormField;
