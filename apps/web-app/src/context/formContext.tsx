'use client';
import { createContext, useContext, useState } from 'react';

const FormContext = createContext(null);

export function FormProvider({ children }) {
  const [formData, setFormData] = useState({});

  const updateForm = (data) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  return (
    <FormContext.Provider value={{ formData, updateForm }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormData() {
  return useContext(FormContext);
}